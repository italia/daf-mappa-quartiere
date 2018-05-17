import React, { Component } from "react";
import BarChart2 from './BarChart2';
import LegendList from './LegendList';

class BarChart2WithLegend extends Component {
    constructor(props) {
	super(props);
    }

    render() {
	var self = this;
	var data = this.props.labels.map((l, i) => {
	    return {
		label: l,
		left: self.props.data1.values[i],
		right: self.props.data2.values[i]
	    };
	});
	
	return (
            <g>
		<text x="0" y="140" style={{fontWeight: "bold"}}>
		    {this.props.title}
	        </text>
		<LegendList
	            label={[self.props.data1.label, self.props.data2.label]}
	            color={[self.props.data1.color, self.props.data2.color]}
	            x={5}
	            y={155}
		/>
		<BarChart2
	            style={{
		        width: 300,
		        height: 370
	            }}
	            barWidth={11}
	            x={50}
	            y={200}
	            data={data}
	            color={{left: self.props.data1.color, right: self.props.data2.color}}
	        />
		<text x="30" y="290" style={{fontSize: 7}}>
		    Sorgente dati: {this.props.dataSource}
	        </text>
            </g>
	);
    };
}

export default BarChart2WithLegend;
