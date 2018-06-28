import React, { Component } from 'react';
import './App.css';
import PieChartWithLegend from './PieChartWithLegend.js';
import BarChart2WithLegend from './BarChart2WithLegend.js';

function sigFigs(n, sig) {
    if (n < 1) {
	var mult = Math.pow(10, sig - Math.floor(Math.log(n) / Math.LN10) - 1);  
	return Math.round(n * mult) / mult;
    } else
	return Math.round(n);
};

class Dashboard extends Component {
    constructor(props: Props) {
	super(props);
	
	this.state = {
	    neighborhood: props.neighborhood
	};
    };

    //otherwise it's updated at each mouse move
    shouldComponentUpdate(nextProps) {
	if (nextProps.neighborhood !== this.props.neighborhood)
	    return true;
	return false;
    };
	
    render() {	
	if (this.props.neighborhood === "none") {
	    return (
		<div
                    className='dashboard-overlay'
		    id='dashboard-start'>
		    Clicca su un quartiere
		</div>
	    );
	}
	var piechartsY = this.props.dashboard.piechart.length * 100;
	
	//to do add IDquartiere in Milano_dashboard.json
	var properties = this.props.neighborhood;
	return (
	    <div className='dashboard-overlay' id='dashboard'>
	        <div>
		    <h3 style={{textAlign: 'left'}}>
		        {properties[this.props.nameField]}
		    </h3>
		    <ul style={{textAlign: 'left', padding: 0}}>
	                {
		            this.props.dashboard.list
				.map(l => {
				    
				    return (
					    <li>
					        {l.label} : {sigFigs(this.props.dashboard.data[this.props.neighborhood.IDquartiere-1][l.field], 2)}
				            </li>
				    );
	                        })
			}
		    </ul>
		</div>
		
		<svg width='445' height='950'>
	            {
		        this.props.dashboard.barchart2
			    .map((d, i) => {
				var data1 = {
				    values: d.data1.fields.map(f => this.props.dashboard.data[this.props.neighborhood.IDquartiere-1][f]),
				    color: d.data1.color,
				    label: d.data1.label
				};
				var data2 = {
				    values: d.data2.fields.map(f => this.props.dashboard.data[this.props.neighborhood.IDquartiere-1][f]),
				    color: d.data2.color,
				    label: d.data2.label
				};
				return (
					<BarChart2WithLegend
				            key={i + "bar"}
				            y={20 + i*200}
				            title={d.label}
				            data1={data1}
				            data2={data2}
				            labels={d.labels}
					    dataSource={this.props.dashboard.dataSource}
					/>
				)})
		    }
	            {
                        this.props.dashboard.piechart
                            .map((p, i) => {
                                var values = p.fields.map(f => this.props.dashboard.data[this.props.neighborhood.IDquartiere-1][f]);
				
                                return (
                                        <PieChartWithLegend
                                            key={i}
                                            y={350 + i*200 + 15}
                                            title={p.label}
                                            labels={p.labels}
                                            values={values}
                                            colors={p.colors}
                                            dataSource={this.props.dashboard.dataSource}
                                         />
                                )})
                    }

		</svg>
	    </div>
	);
    };
}

export default Dashboard;
