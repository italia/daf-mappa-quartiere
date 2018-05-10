import React, { Component } from "react";
import PieChart from './Piechart';
import LegendList from './LegendList';

class PieChartWithLegend extends Component {
    constructor(props) {
	super(props);

	this.state = {
	    title: props.title,
	    labels: props.labels,
	    values: props.values,
	    colors: props.colors
	};
    }

    render() {
	var self = this;
	var seq = Array.from(Array(this.state.values.length).keys());
	
	var data = seq.map((tag, i) => {
	    
	    var label = self.state.labels[i];
	    var value = self.state.values[i];
	 
	    return {tag: i, label: label, value: value}
	}); 
	
	return (
	    <g>
	        <text x="0" y="15" style={{fontWeight: "bold"}}>
		    {this.state.title}
	        </text>
	        <LegendList
	            label={this.state.labels} 
	            color={this.state.colors} 
                    x={5}
                    y={40} 
                />
	        <PieChart
	            x={220}
	            y={65}
	            innerRadius={0}
	            data={data}
	            color={this.state.colors}
	        />
		<text x="100" y="110" style={{fontSize: 7}}>
		    Sorgente dati: {this.props.dataSource}
	        </text>
	    </g>
        );
    };
}

export default PieChartWithLegend;
