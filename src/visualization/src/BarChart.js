import React, { Component } from 'react';
import './App.css';
import { format } from 'd3-format';
import { max, min } from 'd3-array';
import { select } from 'd3-selection';
import { scaleLinear } from 'd3-scale';
import { transition } from 'd3-transition';
import { axisBottom } from 'd3-axis';
import Legend from './Legend';

function sigFigs(n, sig) {
    if (n < 10) {
	var mult = Math.pow(10, sig - Math.floor(Math.log(n) / Math.LN10) - 1);
	return Math.round(n * mult) / mult;
    } else 
	return Math.round(n);
}

class BarChart extends Component {
    yScale;
    
    constructor(props) {
	super(props);

	this.x = 10;
	this.y = 30;

	this.barWidth = Math.min(15, Math.max(window.innerHeight / (this.props.data.values.length * 1.3), 7)),

	this.state = {
	    clicked: props.clicked,
	    hoverElement: props.hoverElements
	};
	
	this.createBarChart = this.createBarChart.bind(this);
	this.visibilityClick = this.visibilityClick.bind(this);
	this.visibilityHover = this.visibilityHover.bind(this);
    };
    
    setYScale() {
	const dataMax = max(this.props.data.values.map(d => d[1]));
	this.yScale = scaleLinear()
            .domain([0, dataMax])
            .range([0, 200]);
    };

    visibilityHover(d, i) {
	return (this.state.hoverElement === d[0]) ? "visible" : "hidden";
    };

    visibilityClick(d, i) {
	return (this.state.clicked === d[0]) ? "visible" : "hidden";
    };

    colorHover() {
	return "black";
    };

    colorClick() {
	return "red";
    };

    classClick() {
	return "click";
    };

    classHover() {
	return "hover";
    };
        
    createTooltip(visibilityCallback, colorCallback, classCallback) {
	const chartContainer = this.chartContainer;

	var size = 11;
	select(chartContainer)
	    .selectAll("rect.tooltip" + classCallback())
	    .data(this.props.data.values)
	    .enter() 
	    .append("rect")
	    .attr("class", "tooltip" + classCallback());
	select(chartContainer)
	    .selectAll("rect.tooltip" + classCallback())
	    .data(this.props.data.values)
	    .exit()
	    .remove();
	select(chartContainer)
	    .selectAll("rect.tooltip" + classCallback())
	    .data(this.props.data.values)   
	    .attr("x", (d) =>  this.x + this.yScale(d[1]) + 60) 
	    .attr("y",  (d, i) => this.y + (i + 0.5) * this.barWidth - 1.2 / 2 * size)
	    .attr("width", (d) => (sigFigs(d[1], 2).toString().length + 1) * size * 0.7)
	    .attr("height", size)
	    .style("fill", colorCallback)
	    .style("fill-opacity", "1")
	    .style("visibility", visibilityCallback);

	select(chartContainer)
            .selectAll("text.tooltip" + classCallback())
            .data(this.props.data.values)
            .enter()
            .append("text")
            .attr("class", "tooltip" + classCallback());
        select(chartContainer)
            .selectAll("text.tooltip" + classCallback())
            .data(this.props.data.values)
            .exit()
            .remove();
        select(chartContainer)
            .selectAll("text.tooltip" + classCallback())
            .data(this.props.data.values)
            .attr("text-anchor", "left")
            .attr("x", d => this.x + this.yScale(d[1]) + 60 + size * 0.7)
            .attr("y", (d, i) => this.y + 0.3 * size + (i + 0.5) * this.barWidth)
            .text(d => sigFigs(d[1], 2))
            .style("visibility", visibilityCallback)
            .style("font-size", size + "px")
            .style("fill", "white");
	
	select(chartContainer)
	    .selectAll("line.tooltip" + classCallback())
	    .data(this.props.data.values)
            .enter()
            .append("line")
            .attr("class", "tooltip" + classCallback());
	select(chartContainer)
            .selectAll("line.tooltip" + classCallback())
            .data(this.props.data.values)
            .exit()
            .remove();
        select(chartContainer)
            .selectAll("line.tooltip" + classCallback())
            .data(this.props.data.values)
	    .attr("x1", d => this.x + this.yScale(d[1])) //+ (sigFigs(d[1], 2).toString().length + 1) * size * 0.7 - size * 0.7)
            .attr("y1", (d, i) => this.y + (i + 0.5) * this.barWidth)
            .attr("x2", d => this.x + 60 + this.yScale(d[1]))
            .attr("y2", (d, i) => this.y + (i + 0.5) * this.barWidth)
	    .style("stroke", colorCallback)
	    .style("stroke-width", "1.5px")
	    .style("visibility", visibilityCallback);
    };

    setLabel() {	
	select(".bartitle").remove();
	select(this.chartContainer).selectAll(".dataSource").remove();
	const chartContainer = this.chartContainer;
        select(chartContainer)
            .append("text")
            .attr("class", "bartitle")
            .attr("x", 10)
            .attr("y", 20)
            .text(this.props.data.label);
	select(chartContainer)
            .append("text")
	    .attr("class", "dataSource")
            .attr("x", 50)
            .attr("y", this.barWidth * (this.props.data.values.length + 2))
	    .text("Sorgente dati: " + this.props.data.dataSource);

    };

    createBarChart() {
	this.setLabel();
	this.setYScale();
	
	const chartContainer = this.chartContainer;
	
	select(chartContainer)
	    .append("text")
	    .attr("id", "description");
	
	select(chartContainer)
	    .append("text")
	    .attr("id", "property")
	    .attr("x", 20)
	    .attr("y", 60 + this.barWidth * 2);
	
	select(chartContainer)
	    .selectAll("rect.bar")
	    .data(this.props.data.values)
	    .enter()
	    .append("rect")
	    .attr("class", "bar")
	    .on("mouseover", d => {
		this.setState({ hoverElement: d[0] });
		this.props.onHover(d);
	    })
	    .on("mouseout", d => {
		this.setState({ hoverElement: "none" });
		this.props.onMouseOut(d);
	    });
	
	select(chartContainer)
	    .selectAll("rect.bar")
	    .data(this.props.data.values)
	    .exit()
	    .remove();
	
	select(chartContainer)
	    .selectAll("rect.bar")
	    .data(this.props.data.values)
	    .attr("y", (d, i) => this.y + i * this.barWidth)
	    .attr("x", d => this.x)
	    .attr("width", d => this.yScale(d[1]))
	    .attr("height", this.barWidth)
	    .style("fill", d => {
		return this.state.hoverElement === d[0] ? "black" : this.props.data.colors.scale(d[1]);
	    })
	    .style("stroke", "black")
	    .style("stroke-opacity", 0.25)
	    .on("click", d => {
		this.setState({ clicked: d[0] });
		this.props.onClick(d);
	    });
	
	this.createTooltip(this.visibilityHover, this.colorHover, this.classHover);
	this.createTooltip(this.visibilityClick, this.colorClick, this.classClick);

	if (this.state.clicked === "none") {
            select(chartContainer).selectAll("rect.tooltipclick").remove();
            select(chartContainer).selectAll("text.tooltipclick").remove();
            select(chartContainer).selectAll("line.tooltipclick").remove();
        }
    };
  
    componentWillReceiveProps(nextProps) {
	if (this.props.clicked !== nextProps.clicked) {
	    this.setState({ clicked: nextProps.clicked });
	}
	if (this.props.hoverElement !== nextProps.hoverElement) {
	    this.setState({ hoverElement: nextProps.hoverElement });
	}
    };
    
    componentDidMount() {
	this.createBarChart();
    };
    
    render() {
	this.createBarChart();
		
	return (<div>
		<svg className="BarChart"
                   ref={el => this.chartContainer = el}
		/>
		<Legend
                        stops={this.props.data.colors.stops}
                        style={{
                            width: 300,
                            height: 40
			}}
                />
		</div>
	);
    };
}

export default BarChart;
