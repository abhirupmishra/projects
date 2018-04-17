#include "StdNormalCDF.h"
#define _USE_MATH_DEFINES
#include "math.h"

StdNormalCDF::StdNormalCDF() {}
StdNormalCDF::~StdNormalCDF() {}

double StdNormalCDF::operator()(double x) const {
	double temp = fabs(x);
	double z = 1 / (1 + 0.2316419*temp);
	double Rz = A1*z + A2*pow(z, 2) + A3*pow(z, 3) + A4*pow(z, 4) + A5*pow(z, 5);
	double result = (1 - (1 / sqrt(2 * M_PI))*exp(-pow(temp, 2) / 2)*Rz);
	if (x >= 0) return result;
	else return (1 - result);
}