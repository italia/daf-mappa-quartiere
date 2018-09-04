import React, { Component } from 'react';

class CityMenu extends Component {
    cityMenu;
    sourceIndex;
    defaultLayerIndex;
    categories;
    joinField;
    
    constructor(props) {
	super(props);
	
	this.cityMenu = props.menu.filter((l) => l.city === props.city);
	this.source = this.getIndex({type: "source"});
	this.host = props.host;
    };
/*
    fetch(v) {
	var index = v[0];
	var indicatorIndex = v[1];
	if (indicatorIndex === undefined) {
	    return fetch(this.host + this.cityMenu.get(index).url)
		.then(response => response.json())
                .then(json => { return { index: index, json: json }; });
	} else {
	    return fetch(this.host + this.cityMenu.get(index).indicators[indicatorIndex].raw.url)
		.then(response => response.json())
		.then(json => { return { index: index, indicatorIndex: indicatorIndex, json: json }; });
	}
    }
*/	
    fetch() {
	return this.cityMenu.reduce((a, l, index) => {
            if (l.indicators !== undefined && l.indicators.length > 0) {
		l.indicators.forEach((i, indicatorIndex) => {
		    if (i.raw != undefined) {
			a.push({ url: this.host + i.raw.url, layerIndex: [index, indicatorIndex] });
                    } 
		});
            }
	    a.push({ url: this.host + l.url, index: index });
            return a;
	}, []).map((a) => {
	    return fetch(a.url)
		.then(response => response.json())
		.then(json => {
		    if (a.index !== undefined) {
			return { index: a.index, json: json };
		    } else {
			return { layerIndex: a.layerIndex, json: json };  
		    }
		})
	});
    };
    
    get(i) {
	return this.cityMenu[i];
    };
    
    getIndex(s) {
	if (s.type !== undefined && s.type === "source") {
	    return this.cityMenu
		.map((l) => l.type)
		.indexOf(s.type);
	}
	if (s.type !== undefined && s.default !== undefined && s.type=== "layer" && s.default) {
	    return this.cityMenu.map((l, index) => {
		var indicatorIndex = -1;
		if (l.indicators !== undefined) {
		    indicatorIndex = l.indicators.map((d) => d.default).indexOf(true);
		}
		return [index, indicatorIndex];
            })
		.filter((l) => l[1] > -1)[0];
	}
	if (s.category !== undefined) {
	    return this.cityMenu.reduce((a, l, index) => {	
		if (l.indicators !== undefined) {
		    l.indicators.forEach((i, indicatorIndex) => {
			if (i.category === s.category) {
			    a.push([index, indicatorIndex]);
			}
		    });
		}
		return a;
	    }, []);
	}
	if (s.id !== undefined && s.indicatorId !== undefined) {
	    return this.cityMenu.reduce((a, l, index) => {
		if (l.indicators !== undefined && l.indicators.length > 0 && l.id === s.id) {
		    l.indicators.forEach((i, indicatorIndex) => {
			if (i.id === s.indicatorId) {
			    a.push([index, indicatorIndex]);
			}
		    });
		}
		return a;
	    }, []);
	}
	if (s.label !== undefined) {
	    return this.cityMenu.map((l, index) => {
		var indicatorIndex = -1;
		if (l.indicators !== undefined) {
                    indicatorIndex = l.indicators.map((d) => d.label).indexOf(s.label);
		}
                return [index, indicatorIndex];
            })
		.filter((l) => l[1] > -1)[0];
	}
    };

    getCategories() {
	var categories = [];
        this.cityMenu.forEach((l) => {
	    if (l.indicators !== undefined) {
                l.indicators
                    .map((i) => i.category)
                    .forEach((c) => {
                        if (categories.indexOf(c) === -1)
                            categories.push(c);
                    })
            }
        });
	return categories;
    };

    getSource(index) {
	return this.cityMenu[index];
    };
    
    getLayer(index) {
	return this.cityMenu[index[0]].indicators[index[1]];
    };

    getCategoryMenu(category) {
        return this.getIndex({"category": category})
            .map((index) => {
		return this.getLayer(index).label;
            });
    };

    getLayerIds() {
	var ids = [];
        this.cityMenu.filter((m) => (m.indicators.length > 0))
            .forEach((m) => { m.indicators.forEach((i) => ids.push(i.id))});
        return ids;
    };

    getLayerLabels() {
	var labels = [];
        this.cityMenu.filter((m) => (m.indicators.length > 0))
            .forEach((m) => { m.indicators.forEach((i) => labels.push(i.label))});
        return labels;
    };
    
    render() {
	return null;
    };
};

export default CityMenu;
