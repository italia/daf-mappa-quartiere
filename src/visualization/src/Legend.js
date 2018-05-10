import React, { Component } from 'react';
import './App.css';
import { select } from 'd3-selection';
import { max, min } from 'd3-array';
import { axisBottom } from 'd3-axis';
import { scaleLinear } from 'd3-scale';

class Legend extends Component {

    componentDidMount() {
	const legendContainer = this.legendContainer;
	
	var values = this.props.stops.map(d => d[0]),
	    minValue = min(values),
	    maxValue = max(values);
	
	var bar = select(legendContainer)
	    .append("defs")
	    .append("svg:linearGradient")
	    .attr("id", "gradient")
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
	    .attr("id", "legend")
	    .attr("width", this.props.style.width)
	    .attr("height", this.props.style.height)
	    .style("fill", "url(#gradient)")
	    .attr("transform", "translate(0,0)");

	var y = scaleLinear()
	    .range([this.props.style.width, 0])
	    .domain([maxValue, minValue]);

	var yAxis = axisBottom()
	    .scale(y)
	    .ticks(5);

	select(legendContainer)
	    .append("g")
	    .attr("class", "axis")
	    .attr("transform", "translate(0,40)")
	    .call(yAxis);
	
    };
    
    render() {
      return  <svg className="Legend"
                  ref={el => this.legendContainer = el}
	      />
  };
}

export default Legend;
