#include "blsprice.h"

using namespace std;

blsprice::blsprice() {}
blsprice::~blsprice() {}

double blsprice::operator() (string type, double spot, double strike, double sigma, double maturity, double rate, double dividend) {
	StdNormalCDF N;
	double d1 = (log(spot / strike) + (rate - dividend + pow(sigma, 2) / 2)*maturity) / (sigma*sqrt(maturity));
	double d2 = d1 - sigma*sqrt(maturity);

	if (type == "call") {
		return ((spot*exp(-dividend*maturity)*N(d1)) - (strike*exp(-rate*maturity)*N(d2)));
	}

	else if (type == "put") {
		return (-spot*exp(-dividend*maturity)*N(-d1) + strike*exp(-rate*maturity)*N(-d2));
	}
	else return -1;
}


double blsprice::delta(string type, double spot, double strike, double sigma, double maturity, double rate, double dividend)
{
	StdNormalCDF N;
	double d1 = (log(spot / strike) + (rate - dividend + pow(sigma, 2) / 2)*maturity) / (sigma*sqrt(maturity));
	if (type == "call") return (exp(-1 * dividend*maturity)*N(d1));
	else if (type == "put") return ((exp(-1 * dividend*maturity)*N(d1)) - 1);
	else return -2.0;
}
