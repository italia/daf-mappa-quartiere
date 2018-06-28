import React, { Component } from 'react';

class MenuObject extends Component {
    constructor(props) {
	super(props);

	this.data = props.data;
	this.layers = this.getLayers();
        this.sources = this.getSources();
        this.cities = this.getCities();

        this.sanityCheck();	
    };

    getLayers(city) {
	if (city !== undefined) {
	    return this.layers.filter(i => i.city === city);
	}

	var self = this;

	var layers = [];
	self.data.forEach(m => {
	    if (m.indicators === undefined)
		return {};
	    layers = layers.concat(m.indicators.map(c => {
		if (m.type === "source") {
		    return {
			id: c.id,
			label: c.label,
			category: c.category,
			sourceId: m.id,
			sourceUrl: m.url,
			city: m.city,
			dataSource : m.dataSource,
			default: c.default
		    };
		} else if (m.type === "layer") {
		    var dataSource = (c.dataSource === undefined) ? m.dataSource : c.dataSource;
		    var sourceUrl = self.data.filter(d => d.id === m.sourceId)[0].url;
		    return {
			id: c.id,
			label: c.label,
			category: c.category,
			layerId: m.id,
			layerUrl: m.url,
			sourceId : m.sourceId,
			dataSource : dataSource,
			sourceUrl: sourceUrl,
			city: m.city,
			default: c.default,
			labels: c.labels,
			colors: c.colors,
			highlight: c.highlight,
			raw: c.raw,
			description: c.description
		    };
		} else {
		    console.log("unknown type in menu");
		}
	    }))
	});

	return layers;

    };

    getSources() {
	return this.data
	    .filter(m => m.type === "source");
    };

    getCities(){
	return this.layers
	    .map(i => i.city)
	    .filter(onlyUnique);
    };

    getCategories(city) {
	var cityLayers = this.layers.filter(i => i.city === city);
	var categories = cityLayers.map(i => i.category)
	    .filter(onlyUnique)
	    .map(c => {
		var subcategories = cityLayers.filter(i => i.category === c);
		return { category: c, subcategories: subcategories };
	    });
	return categories;
    };

    getDefaultLayer(city) {
	return this.getLayers(city)
	    .filter(l => (l.default !== undefined && l.default))[0];
    };

    getDefaultSource(city, sourceId) {
	return this.sources
	    .filter(i => i.city === city)
	    .filter(s => s.id === sourceId)[0];
    };

    sanityCheck() {
	if (this.cities.length === 0) {
	    console.log("no cities in the menu");
	}

	var eachCityHasOneDefaultLayer = this.cities
	    .map(city => this.layers
		 .filter(i => i.city === city)
		 .filter(l => (l.default !== undefined && l.default))
		 .length === 1)
	eachCityHasOneDefaultLayer
	    .forEach((l, i) => {
		if (l === 0)
		    console.log("city " + this.cities(i) + " doesn't have one default layer");
	    });

	var eachCityHasOneDefaultSource = this.cities
	    .map(city => this.sources
		 .filter(i => i.city === city)
		 .filter(l => (l.default !== undefined && l.default))
		 .length === 1)
	eachCityHasOneDefaultSource
	    .forEach((s, i) =>{
		if (s === 0)
		    console.log("city " + this.cities(i) + " doesn't have one default source");
	    });
    };

    render() {
	return null;
    };
};


function onlyUnique(value, index, self) {
    return self.indexOf(value) === index;
};

export default MenuObject;
