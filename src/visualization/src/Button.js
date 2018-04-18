import React, { Component } from 'react';
import './App.css';

class Button extends Component {
  render() {
      return  <button
                  className="btn btn-default"
                  style={{justifyContent: "flex-end", float: "right"}}    
                  onClick={e => this.props.handleClick(e, this.props.label)}>
	          {this.props.label}
	      </button>
  };
}

export default Button;
