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
	        <text x="0" y="15" style={{fontWeight: "bold"}}>
		    {this.props.title}
	        </text>
	        <LegendList
	            label={this.props.labels} 
	            color={this.props.colors} 
                    x={5}
                    y={40} 
                />
	        <PieChart
	            x={220}
	            y={65}
	            innerRadius={0}
	            data={data}
	            color={this.props.colors}
	        />
		<text x="100" y="112" style={{fontSize: 7}}>
		    Sorgente dati: {this.props.dataSource}
	    </text>
	
	    </g>
        );
    };
}

export default PieChartWithLegend;
