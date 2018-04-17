#pragma once
#include "vector"
#include "string"
#include "ql/quantlib.hpp"

using namespace std;
using namespace QuantLib;

class Commons
{
public:
	Commons();
	virtual ~Commons();
	void toCSV(vector<vector<string>> &, vector<string> &, string, string) const;
	vector<double> MonteCarlo(double spot, double mu, double sigma, double T);
	void readCSV(const string& csv, vector<string>& v);
	void readCSV(const string& csv, vector<string>& v1, vector<string>& v2);
	double stringToDouble(string s);
	string doubleToString(double d);
	string DateToString(Date);

protected:

private:
};