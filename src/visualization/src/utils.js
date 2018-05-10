function sigFigs(n, sig) {
    if (n < 1) {
	var mult = Math.pow(10, sig - Math.floor(Math.log(n) / Math.LN10) - 1);
	return Math.round(n * mult) / mult;
    } else {
	return Math.round(n);
    } 
}

export default sigFigs;
