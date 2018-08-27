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
    };

    fetch(params) {
	return this.cityMenu.map((l) => {
            return fetch(params.localhost + l.url)
		.then(response => response.json())
	})
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
		if (l.indicators !== undefined) {
		    var indicatorIndex = l.indicators.map((d) => d.default).indexOf(true);
                    return [index, indicatorIndex];
		} else {
                    return [index, -1];
		}
            })
		.filter((l) => l[1] > -1)[0];
	};
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
	};
	if (s.label !== undefined) {
	    return this.cityMenu.map((l, index) => {
		if (l.indicators !== undefined) {
                    var indicatorIndex = l.indicators.map((d) => d.label).indexOf(s.label);
                    return [index, indicatorIndex];
		} else {
                    return [index, -1];
		}
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
