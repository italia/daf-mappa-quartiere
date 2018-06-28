import React, { Component } from "react";
import BarChart2 from './BarChart2';
import LegendList from './LegendList';

class BarChart2WithLegend extends Component {
    constructor(props) {
	super(props);
    }

    render() {
	var self = this;
	var data = self.props.labels.map((l, i) => {
	    return {
		label: l,
		left: self.props.data1.values[i],
		right: self.props.data2.values[i]
	    };
	});
	var y = self.props.y;
	var barWidth = 11;

	return (
            <g>
		<text x="0" y={y} style={{fontWeight: "bold"}}>
		    {self.props.title}
	        </text>
		<LegendList
	            label={[self.props.data1.label, self.props.data2.label]}
	            color={[self.props.data1.color, self.props.data2.color]}
	            x={5}
	            y={y + 20}
		/>
		<BarChart2
	            style={{
		        width: 300,
		        height: 370
	            }}
	            barWidth={barWidth}
	            x={50}
	            y={y + 65}
	            data={data}
	            color={{left: self.props.data1.color, right: self.props.data2.color}}
	        />
		<text x="30" y={y + 90 + data.length * barWidth} className="dataSource">
		    Sorgente dati: {self.props.dataSource}
	        </text>
            </g>
	);
    };
}

export default BarChart2WithLegend;
