#pragma once
#include <string>
#include "StdNormalCDF.h"
#include "string"
#include "math.h"
#include "cmath"
#include "cstdlib"
#include "iostream"


using namespace std;

class blsprice
{
public:
	blsprice();
	virtual ~blsprice();
	double operator() (string type, double spot, double strike, double sigma, double maturity, double rate, double dividend);
	double delta(string type, double spot, double strike, double sigma, double maturity, double rate, double dividend);

protected:

private:
};