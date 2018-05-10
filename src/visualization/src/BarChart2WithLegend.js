import React, { Component } from "react";
import BarChart2 from './BarChart2';
import LegendList from './LegendList';

class BarChart2WithLegend extends Component {
    constructor(props) {
	super(props);

	this.state = {
	    title: props.title,
	    data1: props.data1,
	    data2: props.data2,
	    labels: props.labels
	};
    }

    render() {
	var self = this;
	var data = this.state.labels.map((l, i) => {
	    return {
		label: l,
		left: self.state.data1.values[i],
		right: self.state.data2.values[i]
	    };
	});
	
	return (
            <g>
		<text x="0" y="140" style={{fontWeight: "bold"}}>
		    {this.state.title}
	        </text>
		<LegendList
	            label={[self.state.data1.label, self.state.data2.label]}
	            color={[self.state.data1.color, self.state.data2.color]}
	            x={5}
	            y={155}
		/>
		<BarChart2
	            style={{
		        width: 300,
		        height: 370
	            }}
	            barWidth={11}
	            x={20}
	            y={200}
	            data={data}
	            color={{left: self.state.data1.color, right: self.state.data2.color}}
	        />
		<text x="30" y="340" style={{fontSize: 7}}>
		    Sorgente dati: {this.props.dataSource}
	        </text>
            </g>
	);
    };
}

export default BarChart2WithLegend;
