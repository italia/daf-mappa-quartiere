import React, { Component } from 'react';
import './App.css';
import { format } from 'd3-format';
import { max, min } from 'd3-array';
import { select, selectAll } from 'd3-selection';
import { scaleLinear } from 'd3-scale';
import { transition } from 'd3-transition';

function sigFigs(n, sig) {
    if (n < 1) {
	var mult = Math.pow(10, sig - Math.floor(Math.log(n) / Math.LN10) - 1);
	return Math.round(n * mult) / mult;
    } else 
	return Math.round(n);
}

class BarChart2 extends Component {
    
    constructor(props: Props) {
	
	super(props);
	
	//set histogram parameters
	this.barLength = props.style.width / 4; //max length of histogram bars
	this.barDistance = this.barLength / 2; //distance between left and right histogram 
	this.fontSize = (props.barWidth - 1) + "px";
	this.random = Math.floor(Math.random() * 100);
	
	this.yBar = this.yBar.bind(this);
    };

    componentDidMount() {
	this.createChart();
    };

    setYScale(maxValue) {	
	this.yScale = scaleLinear()
            .domain([0, maxValue])
            .range([0, this.barLength]);
	
	this.yScale = this.yScale.bind(this);
    };

    yBar(d, i) {
	return this.props.y + i * this.props.barWidth;
    };
    
    createChart() {

	const chartContainer = this.chartContainer;

	//group data of the right histogram and data of the left histogram
	var sum = this.props.data.map(d => d.left).reduce((acc, val) => acc + val);
	sum = sum + this.props.data.map(d => d.right).reduce((acc, val) => acc + val);
	
	this.right = this.props.data.map(d => sigFigs(d.right * 100 / sum, 2));
	this.left = this.props.data.map(d => sigFigs(d.left * 100 / sum, 2));
	
	const maxValue = max([...this.left, ...this.right]);
	this.setYScale(maxValue);
	
	var self = this;
	select(chartContainer)
	    .selectAll("rect.bar.left" + self.random)
	    .data(self.left)
	    .enter()
	    .append("rect")
	    .attr("class", "rect2" + self.random)
            .attr("x", d => self.props.x + self.barLength - self.yScale(d))
	    .attr("y", self.yBar)
            .attr("width", self.yScale)
            .attr("height", self.props.barWidth)
            .style("fill", self.props.color.left)
            .style("stroke", "black");
	
	select(chartContainer)
	    .selectAll("rect.bar.right" + self.random)
	    .data(self.right)
	    .enter()
	    .append("rect")
	    .attr("class", "rect2" + self.random)
	    .attr("x", self.props.x + self.barLength + self.barDistance)
	    .attr("y", self.yBar) 
	    .attr("width", self.yScale)
	    .attr("height", self.props.barWidth)
	    .style("fill", self.props.color.right)
	    .style("stroke", "black");

	select(chartContainer)
	    .selectAll("text.all" + self.random)
	    .data(self.props.data.map(d => d.label))
	    .enter()
	    .append("text")
	    .attr("class", "text2" + self.random)    
	    .attr("x", self.props.x + self.barLength + self.barDistance / 2)
	    .attr("y", (d, i) => self.yBar(d, i) + 0.7 * self.props.barWidth)
	    .style("font-size", self.fontSize)
	    .style("text-anchor", "middle")
	    .text(d => d);

	select(chartContainer)
	    .selectAll("text.left" + self.random)
	    .data(self.left)
	    .enter()
	    .append("text")
	    .attr("class", "text2" + self.random)
	    .attr("x",  d => self.props.x + self.barLength - self.yScale(d) - 2 * (self.props.barWidth - 2))
	    .attr("y", (d, i) => self.yBar(d, i) + 0.7 * self.props.barWidth)
	    .style("font-size", self.fontSize)
	    .style("text-anchor", "middle")
	    .text(d => d + "%");

	select(chartContainer)
            .selectAll("text.right" + self.random)
            .data(self.right)
            .enter()
            .append("text")
	    .attr("class", "text2" + self.random)
            .attr("x",  d => self.props.x + self.barLength + self.barDistance + self.yScale(d) + 2 * (self.props.barWidth - 2))
            .attr("y", (d, i) => self.yBar(d, i) + 0.7 * self.props.barWidth + 1)
            .style("font-size", self.fontSize)
            .style("text-anchor", "middle")
            .text(d => d + "%");
    };
    
    render() {
	selectAll(".rect2" + this.random).remove();
	selectAll(".text2" + this.random).remove();

	this.createChart();
	
	return <svg className="BarChart2"
                   ref={el => this.chartContainer = el}
                   width={this.props.style.width}
                   height={this.props.style.height}
		   />
    };
}

export default BarChart2;
