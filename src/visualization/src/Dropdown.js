import React, { Component } from 'react';
import './App.css';

class DropdownElement extends Component {
    render() {
	return (
	    <a href="#" onClick={e => this.props.handleClick(e, this.props.label)}>
	        {this.props.label}
	    </a>
	);
    }
};

class Dropdown extends Component {
    render() {
        return (
	    <div className="dropdown">
                <button
	            className="dropbtn">
                    {this.props.label}{' '}
	            <i className="fa fa-caret-down"></i>
                </button>
		
                <div className="dropdown-content">
                    {this.props.dropdownContent.map(city => <DropdownElement label={city} handleClick={this.props.handleClick}/>)}
                </div>
            </div>
        );
};
};

export default Dropdown;
