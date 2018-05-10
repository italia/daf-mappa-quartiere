import React, {Component} from 'react';

class LegendPart extends Component {

        createStyle(color) {
            return {fill: color, stroke: "black"};
        }

        render() {
            let transform = "translate(" + this.props.x + "," + this.props.y + ")";
            return (
                <g transform={transform}>
                    <rect width="7" height="7" style={this.createStyle(this.props.color)} rx="1" ry="1" ></rect>
                    <text x="12" y="8">{this.props.label}</text>
                </g>
            );
        }
}

class LegendList extends Component {
    createLegendPart(label, color, x, y) {
	return <LegendPart
	           label={label}
	           color={color}
	           x={x} y={y} />;
    }
    
    createLegend(props) {
        return props.label.map((d, i) => this.createLegendPart(d, props.color[i], props.x, props.y + 22 * i));
    }
    
    render() {
        return (
            <g>
                { this.createLegend(this.props) }
            </g>
        );
    }
}

export default LegendList;
