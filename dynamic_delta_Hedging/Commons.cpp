#define _SCL_SECURE_NO_WARNINGS  
#include "Commons.h"
#include <vector>
#include <string>
#include <iostream>
#include <fstream>
#include <random>
#include "boost/random.hpp"
#include <sstream>
#include <time.h>
#include <cmath>
#include <math.h>
#include <ql/quantlib.hpp>


using namespace std;
using namespace QuantLib;

Commons::Commons() {}
Commons::~Commons() {}

void Commons::toCSV(vector<vector<string>> &data, vector<string> &header, string filename, string path) const {
	unsigned int i, j;

	ofstream outfile;
	outfile.open(path + filename);

	string header_combined = header[0];
	for (i = 1; i < header.size(); i++) {
		header_combined = header_combined + "," + header[i];
	}
	outfile << header_combined + "\n";

	for (i = 0; i < data.size(); i++) {
		string combined = data[i][0];
		for (j = 1; j < data[i].size(); j++) {
			combined = combined + "," + data[i][j];
		}
		outfile << combined + "\n";
	}
	outfile.close();
}


double Commons::stringToDouble(string s) {
	
	double d;
	stringstream ss(s); //turn the string into a stream
	ss >> d; //convert
	return d;
}

//Convert Double to String
string Commons::doubleToString(double d) {
	stringstream strs;
	strs << d;
	string str = strs.str();
	return str;
}

void Commons::readCSV(const string& csv, vector<std::string>& v1, vector<std::string>& v2)
{
	string d;
	ifstream infile(csv);
	bool head = true;
	while (infile.good())
	{
		if (head)
		{
			getline(infile, d, '\n');
			head = false;
		}
		else
		{
			getline(infile, d, ',');
			v1.push_back(d);
			getline(infile, d, '\n');
			v2.push_back(d);
		}

	}
	infile.close();
}

void Commons::readCSV(const string& csv, vector<string>& v)
{
	string d;
	ifstream infile(csv);
	while (infile.good())
	{
		getline(infile, d, '\n');
		v.push_back(d);
	}
	infile.close();
}

vector<double> Commons::MonteCarlo(double spot, double mu, double sigma, double T)
{
	int nsteps = 100;
	double dt, dW;
	vector<double> stock_series;
	default_random_engine generator;

	boost::mt19937 rng;
	boost::normal_distribution<> nd(0.0, 1.0);
	rng.seed(time(0));
	boost::variate_generator<boost::mt19937&, boost::normal_distribution<> > var_nor(rng, nd);

	dt = T / nsteps;
	stock_series.push_back(spot);

	for (int i = 1; i <= nsteps; i++)
	{
		dW = var_nor();
		stock_series.push_back(stock_series[i - 1] * (1 + mu*dt + sigma*sqrt(dt)*dW));
	}
	return stock_series;
};

string Commons::DateToString(Date d) {
	return to_string(d.year()) + "-" + to_string(d.month()) + "-" + to_string(d.dayOfMonth());
}