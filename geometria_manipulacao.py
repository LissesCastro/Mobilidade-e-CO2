
#IMPORTANDO BIBLIOTECAS, AS BIBLIOTECAS SÃO PRINCIPALMENTE PARA MANIPULAÇÃO DO DATAFRAME, EXTRAÇÃO DE DADOS DO SHAPE E CRIAÇÃO DAS GEOMETRIA
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, mapping, shape, Point
import fiona

#CRIANDO AS FUNÇÕES PARA EXTRAÇÃO DE DADOS DO SHAPE E CRIAÇÃO DAS GEOMETRIA
def extrai_centroides_shape(path, feature_id='id', feature_geometria='geometry'):
    '''Recebe o caminho do arquivo .shp e retorna um dicionário 
    com o ID da zona como chave e as posições X e Y do centroide
    como valor. Verificar se os nomes das features estão corretas
    no shape'''
    centroides = []

    with fiona.open(path) as shp:
        for feature in shp:
            id = feature[feature_id]
            geometry = shape(feature[feature_geometria])
            # Get the centroid and add it to the list with the ID
            centroid = geometry.centroid
            centroides.append([int(id), centroid.x, centroid.y])
        dict_centroides = {item[0]: (item[1], item[2]) for item in centroides}
    return dict_centroides

def concatena_centroides_zonas(dataframe, dicionario_centroides, coluna_zona_origem='ZONA_O', coluna_zona_destino='ZONA_D'):
    '''Recebe um dataframe e um dicionário com o id das zonas e o valor dos centróides,
        cria variáveis dos eixos X e Y de origem e destino de acordo com o match entre
        o nome da chave do dicionário e o nome das colunas de origem e destino'''
    for index, row in dataframe.iterrows():
            for key, value in dicionario_centroides.items():
                if row[coluna_zona_origem] == key:
                    dataframe.at[index, 'ZONA_O_X'] = value[0]
                    dataframe.at[index, 'ZONA_O_Y'] = value[1]
                if row[coluna_zona_destino] == key:
                    dataframe.at[index, 'ZONA_D_X'] = value[0]
                    dataframe.at[index, 'ZONA_D_Y'] = value[1]

def cria_linhas_geometria(dataframe, x1='CO_O_X', y1='CO_O_Y', x2='CO_D_X', y2='CO_D_Y'):
    '''Cria linhas de geometria que conectam os pontos de origem 
    a partir das colunas de um dataframe. 
    As colunas devem conter as informações de posição X e Y de origem e destino. 
    Cria retas, logo, requer exatamente dois pontos'''
    geometria = [LineString([(row[x1], row[y1]), (row[x2], row[y2])]) for idx, row in dataframe.iterrows()]
    return geometria

def identifica_corrige_geometrias(geo_dataframe):
    '''Utiliza o módulo shape do Shapely para identificar geometrias inválidas,
        se a geometria não é valida, cria um buffer a partir da geometria'''
    for i, geom in enumerate(geo_dataframe.geometry):
        if not shape(geom).is_valid:
            geo_dataframe.geometry[i] = geom.buffer(0) #Coloca buffer a geometria:
    return geo_dataframe

def transforma_em_string(dataframe,tipo_original):
    '''Função tradicional que seleciona o tipo colocado
        no input e tenta transformar em String'''
    for col in dataframe.select_dtypes(include=[tipo_original]):
        dataframe[col] = dataframe[col].astype('string')
    return dataframe

#CHAMANDO O DATAFRAME A PARTIR DO CSV TRABALHADO NO ARQUIVO "analise.ipynb" DESSE MESMO REPOSITÓRIO
df = pd.read_csv('OD_2017_Trabalhada.csv')

#CRIANDO O DICIONÁRIO QUE CONTÉM AS INFORMAÇÕES DE POSIÇÃO DE CADA CENTROIDE DA GEOMETRIA DAS ZONAS, ADICIONANDO ESSAS INFORMAÇÕES AO DATAFRAME PRINCIPAL E CRIANDO A GEOMETRIA DE LINHA
dict_centroides = extrai_centroides_shape('GIS/Zonas_2017_region.shp')
df = concatena_centroides_zonas(dataframe=df, dicionario_centroides=dict_centroides)
geometria_zonas = cria_linhas_geometria(df, x1='ZONA_O_X', y1='ZONA_O_Y', x2='ZONA_D_X', y2='ZONA_D_Y')

#CRIANDO UM GEODATAFRAME QUE CONTÉM AS INFORMAÇÕES DE POSIÇÃO DO DATAFRAME PRINCIPAL. QGIS NÃO ACEITA O TIPO "CATEGORY", POR ISSO TRANSFORMO EM STRING
gdf_zonas = gpd.GeoDataFrame(df, geometry=geometria_zonas)
gdf_zonas = identifica_corrige_geometrias(gdf_zonas)
gdf_zonas = transforma_em_string(gdf_zonas, 'category')

#EXPORTANDO O SHAPEFILE
gdf_zonas.crs = {'init': 'epsg:4326'}
gdf_zonas.to_file('OD_Zonas_Zonas_Lines.shp', driver='ESRI Shapefile')
