#pragma once
using namespace std;

class StdNormalCDF
{
public:
	StdNormalCDF();
	virtual ~StdNormalCDF();
	double operator() (double) const;

protected:

private:
	const double A1 = 0.319381530;
	const double A2 = -0.356563782;
	const double A3 = 1.781477937;
	const double A4 = -1.821255978;
	const double A5 = 1.330274429;
};