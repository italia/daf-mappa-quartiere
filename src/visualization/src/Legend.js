import React, { Component } from 'react';
import './App.css';
import { select, selectAll } from 'd3-selection';
import { max, min } from 'd3-array';
import { axisBottom } from 'd3-axis';
import { scaleLinear } from 'd3-scale';

class Legend extends Component {
    
    createLegend() {
	//clean
	select("#mapLegend").remove();
	select("#mapAxis").remove();
        select("#mapGradient").remove();

	const legendContainer = this.legendContainer;
	
	var values = this.props.stops.map(d => d[0]),
	    minValue = min(values),
	    maxValue = max(values);
	
	var bar = select(legendContainer)
	    .append("defs")
	    .append("svg:linearGradient")
	    .attr("id", "mapGradient")
	    .attr("x1", "0%")
	    .attr("y1", "100%")
	    .attr("x2", "100%")
	    .attr("y2", "100%")
	    .attr("spreadMethod", "pad");
	
	bar.selectAll(".stop")
	    .data(this.props.stops)
	    .enter()
	    .append("stop")
	    .attr("offset", (d, i, j) => {
		return (100 * i / (j.length - 1)) + "%";
	    })
	    .attr("stop-color", d => d[1])
	    .attr("stop-opacity", 1);

	select(legendContainer)
	    .append("rect")
	    .attr("id", "mapLegend")
	    .attr("width", this.props.style.width / 2)
	    .attr("height", this.props.style.height / 2)
	    .style("fill", "url(#mapGradient)")
	    .attr("transform", "translate(20,0)");

	var y = scaleLinear()
	    .range([this.props.style.width / 2, 0])
	    .domain([maxValue, minValue]);

	var yAxis = axisBottom()
	    .scale(y)
	    .ticks(5);

	select(legendContainer)
	    .append("g")
	    .attr("id", "mapAxis")
	    .attr("class", "axis")
	    .attr("transform", "translate(20,40)")
	    .call(yAxis);
	
    };
    
    render() {
	this.createLegend();
        return  <svg className="Legend"
                    ref={el => this.legendContainer = el}
	            width={this.props.style.width}
	            height={this.props.style.height}
	        />
    };
}

export default Legend;
