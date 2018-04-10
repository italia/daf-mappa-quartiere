import pandas as pd
import geopandas as gpd

def new_index(old_df, lista_col_num, lista_col_den, nome_indice):
    """The function creates a new variable that is obtained by a simple ratio. It returns a df updated
    with the new column.
    
    INPUT:
    @old_df: the df to update
    @lista_col_num: list of columns of the df to sum up to compose the numerator
    @lista_col_den: list of columns of the df to sum up to compose the denominator
    @nome_indice: name of the new column
    
    """
    
    old_df[nome_indice] = old_df[lista_col_num].sum(axis=1)/old_df[lista_col_den].sum(axis=1)
    
    return old_df