import React, { Component } from "react";
import PieChart from './Piechart';
import LegendList from './LegendList';
import { select } from 'd3-selection';

class PieChartWithLegend extends Component {
    constructor(props) {
	super(props);
    }

    render() {
	var self = this;
	var seq = Array.from(Array(this.props.values.length).keys());
	
	var data = seq.map((tag, i) => {
	    var label = self.props.labels[i];
	    var value = self.props.values[i];
	    return {tag: i, label: label, value: value}
	});
	
	return (
	    <g>
	        <text x="0" y={this.props.y} style={{fontWeight: "bold"}}>
		    {this.props.title}
	        </text>
	        <LegendList
	            label={this.props.labels} 
	            color={this.props.colors} 
                    x={5}
                    y={this.props.y + 25} 
                />
	        <PieChart
	            x={280}
	            y={this.props.y + 95}
	            innerRadius={0}
	            data={data}
	            color={this.props.colors}
	        />
		<text x="30" y={this.props.y + 165} className="dataSource">
		    Sorgente dati: {this.props.dataSource}
	    </text>
	
	    </g>
        );
    };
}

export default PieChartWithLegend;
