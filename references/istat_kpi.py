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


def compute_vitality_cpa2011(quartiere_data):
    """Given the dataframe of Ista cpa 2011 (data level: neighborhood)
    for a city, the function returns a new dataframe whose columns are
    KPI computed from CPA 2011 and the rows are the neighborhoods.

    The list of vitality KPI is the following (lang:it):

        1. Building types (tipo di alloggi)

        2. Employement density (densita' di occupati)

    """

    new_columns_names = [
        'tipo_di_alloggi',
        'densita_occupati',
        ]

    out=pd.DataFrame()
    # 1. Building types (average number of floors)
    building_columns = ['E17', 'E18', 'E19', 'E20']
    out[new_columns_names[0]] = (
            [1,2,3,4]*quartiere_data[building_columns]).sum(axis=1) /\
                                quartiere_data[building_columns].sum(axis=1)
    # 2. Employement density
    try:
        val = quartiere_data['P60'] / quartiere_data['SHAPE_AREA']
        val = val/val.mean() #normalize
        out[new_columns_names[1]] = val
    except:
        print('Had to skip employment density')

    return out

def wrangle_istat_cpa2011(quartiere_data, selectedCity):
    """Given the dataframe of Ista cpa 2011 (data level: neighborhood) 
    for a city, the function returns a new dataframe whose columns are
    KPI computed from CPA 2011 and the rows are the neighborhoods. Moreover, the dataframe
    is stored both in a csv and json file.
    
    The list of retrived KPI is the following (lang:it):

        1. @indice_stranieri: Percentuale residenti stranieri.
                                - Sul totale dei residenti

        2. Percentuali di provenienza degli stranieri (*per ogni continente la percentuale è rispetto la popolazione residente straniera*).
            @perc_europei: Europa
            @perc_africa: Africa
            @perc_america: Asia
            @perc_asia: America
            @perc_oceania: Oceania

        3. Indice di vecchiaia: *rapporto tra il numero di residenti di età > 64 e numero residenti che hanno meno di 14 anni.*
            @indice_vecchiaia: Sul totale popolazione
            @indice_vecchiaia_uomo: Tra gli uomini
            @indice_vecchiaia_donna: Tra le donne

        4. Indice di popolazione attiva: *rapporto tra il numero di residenti con età compresa tra i 39 ed i 64 anni e quelli tra i 15 ed i 39.*
            @indice_pop_attiva: Sul totale popolazione
            @indice_pop_attiva_uomo Tra gli uomini
            @indice_pop_attiva_donna: Tra le donne

        5. @indice_pop_pendolare: Popolazione residente che svolge la propria giornata fuori dal comune di residenza sul totale della popolazione residente.

        6. @indice_pop_non_pend_esterna_quartiere: Popolazione residente che svolge la propria giornata nel comune ma fuori dal proprio quartiere

        7. @indice_pop_non_pend_interna_quartiere: Popolazione residente che svolge la propria giornata nel proprio quartiere"""
    
    
    # 1. Creazione indice residenti stranieri
    new_index(quartiere_data, ['ST15'], ['P1'], 'indice_stranieri')
    
    
    # 2. Lista di nomi di variabili che voglio creare 
    list_columns_continenti = ['perc_europei', 'perc_africa', 'perc_america', 'perc_asia', 'perc_oceania']
    # Lista colonne utili dal df di istat
    list_attr_continenti = ['ST9', 'ST10', 'ST11', 'ST12', 'ST13']
    # Calcolare l'indice per ogni continente
    for idx, continente in enumerate(list_columns_continenti):
        new_index(quartiere_data, [list_attr_continenti[idx]], ['ST15'], list_columns_continenti[idx])
    
    
    # 3. Creo la nuova colonna
    new_index(quartiere_data, ['P43', 'P44', 'P45'], ['P30', 'P31', 'P32'], 'indice_vecchiaia_uomo')
    # Creo la nuova colonna
    new_index(quartiere_data, ['P27', 'P28', 'P29'], ['P14', 'P15', 'P16'], 'indice_vecchiaia')
    # Creo la nuova colonna
    new_index(quartiere_data, ['P43', 'P44', 'P45'], ['P30', 'P31', 'P32'], 'indice_vecchiaia_uomo')
    # Calcola numeratore e denominatore
    donne_anziane = quartiere_data[['P27', 'P28', 'P29']].sum(axis=1) - (quartiere_data[['P43', 'P44', 'P45']].sum(axis=1))
    donne_giovani = quartiere_data[['P14', 'P15', 'P16']].sum(axis=1) - quartiere_data[['P30', 'P31', 'P32']].sum(axis=1)
    # Quindi, il nuovo indice
    quartiere_data['indice_vecchiaia_donna'] = donne_anziane / donne_giovani
    
    
    # 4. Creo la nuova colonna
    new_index(quartiere_data, ['P22', 'P23', 'P24', 'P25', 'P26'], ['P17', 'P18', 'P19', 'P20', 'P21'], 'indice_pop_attiva')
    # Creo la nuova colonna
    new_index(quartiere_data, ['P38', 'P39', 'P40', 'P41', 'P42'], ['P33', 'P34', 'P35', 'P36', 'P37'], 'indice_pop_attiva_uomo')
    # Calcolo numeratore e denominatore
    numeratore_donne = (quartiere_data[['P22', 'P23', 'P24', 'P25', 'P26']].sum(axis=1)) - (quartiere_data[['P38', 'P39', 'P40', 'P41', 'P42']].sum(axis=1))
    denominatore_donne = (quartiere_data[['P17', 'P18', 'P19', 'P20', 'P21']].sum(axis=1)) - (quartiere_data[['P33', 'P34', 'P35', 'P36', 'P37']].sum(axis=1))
    # Creazione colonna
    quartiere_data['indice_pop_attiva_donna'] = numeratore_donne / denominatore_donne
    
    
    # 5. Creo la nuova colonna
    new_index(quartiere_data, ['P138'], ['P1'], 'indice_pop_pendolare')
    
    
    # 6. Creo la nuova colonna
    new_index(quartiere_data, ['P137'], ['P1'], 'indice_pop_non_pend_esterna_quartiere')
    
    # 7. Creo nuova colonna
    giornata_dentro_quartiere = quartiere_data['P1'] - (quartiere_data[['P137', 'P138']].sum(axis=1))
    quartiere_data['indice_pop_non_pend_interna_quartiere'] = giornata_dentro_quartiere / quartiere_data['P1']
    
    return quartiere_data