import React, { Component } from "react";
import { select } from "d3-selection";
import { arc, pie } from "d3-shape";

class Arc extends Component {

    tickness = 40;
    
    constructor(props) {
        super(props);

	this.arcLine = arc()
	    .innerRadius(props.innerRadius)
	    .outerRadius(props.innerRadius + this.tickness)
	    .cornerRadius(3);
    };

    render() {

        return (
            <path
                d={this.arcLine(this.props.d)}
                style={{
                    fill: this.props.color,
		    stroke: "black"
                }}
                ref="elem"
            />
        );
    };
}

class Piechart extends Component {
    
    pieChart = pie()
        .value(d => d.value)
        .sortValues(d => d.tag)
        .padAngle(0.005);

    render() {
        const { data, color, innerRadius, x, y} = this.props;
   
        return (
            <g className="Piechart" transform={`translate(${x}, ${y})`}>
                {this.pieChart(data).map((d, i) => ( 
		    <Arc
		        d={d}
		        color={color[i]}
		        key={d.data.tag}
		        innerRadius={innerRadius}
		    />
                ))}
            </g>
        );
    };
}

export default Piechart;
