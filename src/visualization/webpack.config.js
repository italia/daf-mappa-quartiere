const Path = require('path');
const Webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
    devtool: 'inline-source-map',
    entry: [
	'webpack-hot-middleware/client',
	'./src/index.js'
    ],
    output: {
	path: Path.resolve(__dirname, 'dist'),
	filename: 'bundle.js',
	publicPath: '/public/'
    },
    plugins: [
	new Webpack.optimize.OccurrenceOrderPlugin(),
	new Webpack.HotModuleReplacementPlugin()
    ]
};
