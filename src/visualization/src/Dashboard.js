import React, { Component } from 'react';
import './App.css';
import { VictoryChart, VictoryTheme, VictoryGroup, VictoryArea, VictoryPolarAxis, VictoryLabel } from 'victory';

function sigFigs(n, sig) {
    if (n < 10) {
	var mult = Math.pow(10, sig - Math.floor(Math.log(n) / Math.LN10) - 1);
	return Math.round(n * mult) / mult;
    } else
	return Math.round(n);
};

class Dashboard extends Component {
    maxima;
    
    constructor(props: Props) {
        super(props);

        this.state = {
            city: props.city,
            neighborhood: props.neighborhood,
            hoverNeighborhood: props.neighborhood,
            infoElement: "hidden"
        };
    };
    
    componentDidMount() {
	this.maxima = this.props.ids
            .reduce((o, key) => {
		var k = Math.max(...this.props.features.map(f => f.properties[key]));
		k = sigFigs(k, 2);
                return ({ ...o, [key]: k });
	    }, {});
    };
    
    componentWillReceiveProps(nextProps) {
	this.maxima = nextProps.ids
	    .reduce((o, key) => {
		var k = Math.max(...nextProps.features.map(f => f.properties[key]));
		k = sigFigs(k, 2);
		return ({ ...o, [key]: k });
	    }, {});
    };

    getIndexFromNeighborhood(n) {
        var joinField = this.props.joinField;
        return (n === "none") ? "none" : n[joinField];
    };

    shouldComponentUpdate(nextProps, nextState) {
	if (this.props.city !== nextProps.city)
	    return true;
	if (this.getIndexFromNeighborhood(this.props.neighborhood) !== this.getIndexFromNeighborhood(nextProps.neighborhood))
            return true;
	if (this.getIndexFromNeighborhood(this.props.hoverNeighborhood) !== this.getIndexFromNeighborhood(nextProps.hoverNeighborhood))
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
	var mydata = [this.props.ids.map((key) => {return {
            x: key,
            y: this.props.neighborhood[key] / this.maxima[key]
        }})];
     
        if (this.props.hoverNeighborhood !== "none") {
            mydata.push(this.props.ids.map((key) => {return {
                x: key,
                y: this.props.hoverNeighborhood[key] / this.maxima[key]
            }}));
        }
	
	return (
	    <div className='dashboard-overlay' id='dashboard'>
	        <div>
		    <h3>
		        {this.props.neighborhood[this.props.nameField]}
	            </h3>
		<div style={{fontSize: "12px", textAlign: "left"}}>
		        Confronta i diversi indicatori in questo quartiere.
		    </div>
                    <VictoryChart polar 
                        theme={VictoryTheme.material}
                        domain={{ y: [ 0, 1 ] }}
                    >
                        <VictoryGroup colorScale={["red", "black"]}
                            style={{ data: { fillOpacity: 0.2, strokeWidth: 2 } }}
                        >
                            {mydata.map((data, i) => {
                                return <VictoryArea key={i} data={data}/>;
                            })}
                        </VictoryGroup>
                        {
                        Object.keys(this.maxima).map((key, i) => {
                            return (
                                <VictoryPolarAxis key={i} dependentAxis
                                    style={{
                                        axisLabel: { padding: 10 },
                                        axis: { stroke: "none" },
                                        grid: { stroke: "grey", strokeWidth: 0.25, opacity: 0.5 }
                                    }}
                                    tickLabelComponent={
                                        <VictoryLabel labelPlacement="vertical"/>
                                    }
                                    labelPlacement="perpendicular"
                                    axisValue={i + 1} label={this.props.labels[i]}
                                    tickFormat={(t) => Math.ceil(t * this.maxima[key])}
                                    tickValues={[0.25, 0.5, 0.75]}
                                />
                            );
                        })
                        }
                        <VictoryPolarAxis
                            labelPlacement="parallel"
                            tickFormat={() => ""}
                            style={{
                                axis: { stroke: "none" },
                                grid: { stroke: "grey", opacity: 0.5 }
                            }}
                        />

                    </VictoryChart>
	        </div>
	    </div>
	);
    };
}

export default Dashboard;
