export default [
{
    id : "Milano_quartieri",
    city : "Milano",
    type : "source",
    url : "localhost:3000/Milano/NILZone.EPSG4326.json",
    center : [9.191383, 45.464211],
    zoom : 11,
    joinField : "ID_NIL",
    dataSource : "Comune di Milano",
    default : true,
    indicators : [{
	category : "Dati Geografici",
	label : "Area (mq)",
	id : "AreaMQ"
    }]
},{
    id : "Milano_EducazioneCultura",
    indicators : [
        
            {
                category : "Educazione e Cultura",
                id : "School",
                label : "Scuole"
            },
            {
                category : "Educazione e Cultura",
                id : "Library",
                label : "Biblioteche"
            }
        
    ],
    city : "Milano",
    sourceId : "Milano_quartieri",
    type : "layer",
    url : ""
},{
    id : "Milano_istat",
    city : "Milano",
    type : "layer",
    sourceId : "Milano_quartieri",
    dataSource : "ISTAT (censimento 2011 della popolazione e delle abitazioni)",
    url : "localhost:3000/Milano/results.json",
    indicators : [{
	category : "Vitalità",
	label : "Tipo di alloggi",
	id : "tipiAlloggio"
    },{
	category : "Vitalità",
	label : "Densità di occupati (per mq)",
	id : "densitaOccupati",
	default: true
    }]
},{
    id : "Torino_quartieri",
    city: "Torino",
    type : "source",
    url : "localhost:3000/Torino/0_geo_zone_circoscrizioni_wgs84.json",
    dataSource : "tbd",
    center : [7.6869, 45.0703],
    zoom : 10.5,
    joinField : "NCIRCO",
    indicators : [],
    default : true
},{
    id : "Torino_istat",
    city : "Torino",
    type : "layer",
    sourceId : "Torino_quartieri",
    dataSource : "ISTAT (censimento 2011 della popolazione e delle abitazioni)",
    url : "localhost:3000/Torino/results.json",
    indicators : [{
	category : "Vitalità",
	label : "Tipi di Alloggio",
	id : "tipiAlloggio2"
    },{
	category : "Vitalità",
	label : "Densità di occupati (per mq)",
	id : "densitaOccupati2",
	default: true
    },{
	category : "Dati Geografici",
	label : "Area",
	id : "SUPERF"
    },{
	category : "Popolazione",
	label : "Numero di residenti",
	id : "residenti"
    }]
},{
    id : "Torino_istruzione",
    city : "Torino",
    type : "layer",
    sourceId : "Torino_quartieri",
    dataSource : "dati simulati",
    url : "localhost:3000/Torino/istruzione.json",
    indicators : [{
        category : "Popolazione",
        label : "Popolazione residente - analfabeti",
        id : "analfabeti"
    },{
        category : "Popolazione",
        label : "Popolazione residente con licenza elementare",
        id : "elementare"
    },{
        category : "Popolazione",
        label : "Popolazione residente con media inferiore",
        id : "media"
    },{
        category : "Popolazione",
        label : "Popolazione residente con diploma di scuola secondaria superiore (maturità + qualifica)",
        id : "superiore"
    },{
        category : "Popolazione",
        label : "Popolazione residente con laurea vecchio e nuovo ordinamento + diplomi universitari + diplomi terziari di tipo non universitario vecchio e nuovo ordinamento",
        id : "diploma"
    },{
	category : "Istruzione",
	label : "Livello di istruzione",
        id : "istruzione" 
    }]
}
]
    
