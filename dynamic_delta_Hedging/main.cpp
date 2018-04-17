#define _SCL_SECURE_NO_WARNINGS  
#include <iostream>
#include <random>
#include "string"
#include <iostream>
#include <sstream>
#include "Commons.h"
#include "blsprice.h"
#include <algorithm>
#include <ql/quantlib.hpp>

using namespace std;
using namespace QuantLib;

int main()
{
	blsprice bls;
	Commons comm;
	vector<double> stockProcess, callPrices, callDelta, hedgingError, interest, stockPrice, optionPrice;
	vector<string> interestString, stockPriceString, optionPriceString;
	double spt = 100, mu = 0.05, sigma = 0.3, T = 0.4, rate = 0.025, N=100, K = 105, cash=500;
	Calendar usCal = UnitedStates();

	/*Part-1*/
	cout << "****************************Start******************************" << endl;
	stockProcess = comm.MonteCarlo(spt, mu, sigma, T);

	//getting the vector for call option prices
	double dt = T/N;
	
	for (int i = 0; i < stockProcess.size(); i++) 
	{
		double passedTime = i*dt;
		double remainingTime = T - passedTime;
		
		callPrices.push_back(bls("call", stockProcess[i], K, sigma, remainingTime, rate, 0));
		callDelta.push_back(bls.delta("call", stockProcess[i], K, sigma, remainingTime, rate, 0));				
	}

	
	double hedgingErrorTemp = callPrices[0] - callDelta[0] * stockProcess[0];
	//B.push_back(hedgingErrorTemp);
	
	cout << stockProcess.size() << "-" << callDelta.size() << "-" << callPrices.size() << endl;
	
	for (int i = 1; i < stockProcess.size(); i++) {
		double HE = (callDelta[i-1] * stockProcess[i]) + (hedgingErrorTemp*exp(rate*dt)) - callPrices[i];
		hedgingErrorTemp = callDelta[i - 1] * stockProcess[i] + (hedgingErrorTemp*exp(rate*dt)) - (callDelta[i] * stockProcess[i]);
		//B.push_back(hedgingErrorTemp);
		cout << HE << endl;
	}

	cout << "*****************************End*******************************" << endl;
	cout << "Part-1 Done" <<endl;

	/*Part-2*/
	cout << "****************************Start******************************" << endl;
	//reading the csvfile
	comm.readCSV("./interest.csv", interestString);
	comm.readCSV("./sec_GOOG.csv", stockPriceString);
	comm.readCSV("./op_GOOG.csv", optionPriceString);

	cout << interestString.size() << "-" << stockPriceString.size() << "-" << optionPriceString.size() <<endl;

	//Input initial, end , expiry date and strike price from user
	string t0, tn, texp;
	cout << endl << "Enter intial date(yyyy-mm-dd): " << endl;
	cin >> t0;
	cout << endl << "Enter end date(yyyy-mm-dd): " << endl;
	cin >> tn;
	cout << endl << "Enter expiry date(yyyy-mm-dd): " << endl;
	cin >> texp;

	double strike_given;
	cout << endl << "Enter Strike Price: " << endl;
	cin >> strike_given;

	//converting the date strings to date format
	Date initDate, endDate, expDate;
	initDate = DateParser::parseFormatted(t0, "%Y-%m-%d");
	endDate = DateParser::parseFormatted(tn, "%Y-%m-%d");
	expDate = DateParser::parseFormatted(texp, "%Y-%m-%d");
	
	int workingDays = usCal.businessDaysBetween(initDate, endDate, true, true);
	cout <<"Business Days: " << workingDays << endl;

	vector<string> dateVal;

	//filtering the interest data
	for (int i=1; i<interestString.size();i++){
		string line = interestString[i];
		string date_val = line.substr(0, line.find(","));
		
		Date rowDate = DateParser::parseFormatted(date_val, "%Y-%m-%d");
		
		if(rowDate >= initDate && rowDate <= endDate){
			double spot_val = atof(line.substr(date_val.length() + 1, line.length()).c_str());
			interest.push_back((spot_val/100));
			dateVal.push_back(date_val);
		}
	}
	
	//filtering the stock price data
	for (int i = 1; i<stockPriceString.size(); i++) {
		string line = stockPriceString[i];
		string date_val = line.substr(0, line.find(","));

		Date rowDate = DateParser::parseFormatted(date_val, "%Y-%m-%d");

		if (rowDate >= initDate && rowDate <= endDate) {
			double spot_val = atof(line.substr(date_val.length() + 1, line.length()).c_str());
			stockPrice.push_back(spot_val);
		}
	}

	vector<double> mid_price;
	double start = comm.stringToDouble(t0.substr(0, 4) + t0.substr(5, 2) + t0.substr(8, 2));
	double end = comm.stringToDouble(tn.substr(0, 4) + tn.substr(5, 2) + tn.substr(8, 2));
	double ex_date = comm.stringToDouble(texp.substr(0, 4) + texp.substr(5, 2) + texp.substr(8, 2));
	//cout << start << "-"<< end << endl;
	
	//filtering the options price data
	for (int i = 1; i < optionPriceString.size() ; i++) {
		stringstream lineStream(optionPriceString[i]);
		string dateS, exDateS, type, strikeS, bidS, askS;
		double date, exDate, strike, mid;
		int counter = 0;
		
		//loading the csv file
		getline(lineStream, dateS, ',');
		getline(lineStream, exDateS, ',');
		getline(lineStream, type, ',');
		getline(lineStream, strikeS, ',');
		getline(lineStream, bidS, ',');
		getline(lineStream, askS, ',');
		
		//typecasting
		date = comm.stringToDouble(dateS.substr(0, 4) + dateS.substr(5, 2) + dateS.substr(8, 2));
		exDate = comm.stringToDouble(exDateS.substr(0, 4) + exDateS.substr(5, 2) + exDateS.substr(8, 2));
		strike = atof(strikeS.c_str());

		if(date >= start && date <= end && exDate == ex_date && type == "C" && strike == strike_given){
			mid = (atof(bidS.c_str()) + atof(askS.c_str())) / 2.0;
			mid_price.push_back(mid);
			//cout << "date: " << dateS << " exDate: " << exDateS << " type: " << type << " Strike: " << strikeS << " bidS: " << bidS << " askS: " << askS << endl;
			if (end == date) break;
		}
		else continue;		
	}
	
	//parameters for implied volatility computation
	Size maxEvaluations = 1000;
	Real tolerance = 1.0e-4, upper = 1.0;
	DayCounter dc = Business252();
	
	vector<string> impVolVector, DeltaVector;

	for (int i = 0; i < dateVal.size(); i++) {		
		Date today = DateParser::parseFormatted(dateVal[i], "%Y-%m-%d");
		Settings::instance().evaluationDate() = today;
		
		//cout << Settings::instance().evaluationDate() << endl;
		
		boost::shared_ptr<SimpleQuote> spot(new SimpleQuote(0.0));
		boost::shared_ptr<SimpleQuote> qRate(new SimpleQuote(0.0));
		boost::shared_ptr<YieldTermStructure> qTS(new FlatForward(today, Handle<Quote>(qRate), dc));
		boost::shared_ptr<SimpleQuote> rRate(new SimpleQuote(0.0));
		boost::shared_ptr<YieldTermStructure> rTS(new FlatForward(today, Handle<Quote>(rRate), dc));
		boost::shared_ptr<SimpleQuote> vol(new SimpleQuote(0.0));
		boost::shared_ptr<BlackVolTermStructure> volTS(new BlackConstantVol(today, usCal, Handle<Quote>(vol), dc));

		Real rfr = interest[i];
		Real K = strike_given;
		Real U = stockPrice[i];
		Real p = mid_price[i];
		Date exp = expDate;

		boost::shared_ptr<StrikedTypePayoff> payoff(new PlainVanillaPayoff(Option::Type::Call, K));
		boost::shared_ptr<Exercise> exercise(new EuropeanExercise(exp));
		
		spot->setValue(U);
		rRate->setValue(rfr);
		
		boost::shared_ptr<BlackScholesMertonProcess> stochProcess(new
			BlackScholesMertonProcess(Handle<Quote>(spot),
				Handle<YieldTermStructure>(qTS),
				Handle<YieldTermStructure>(rTS),
				Handle<BlackVolTermStructure>(volTS)));
		
		boost::shared_ptr<PricingEngine> engine(new AnalyticEuropeanEngine(stochProcess));
		EuropeanOption option(payoff, exercise);
		option.setPricingEngine(engine);
		
		Real implVol = 0;
		try{
			implVol = option.impliedVolatility(p, stochProcess, tolerance, maxEvaluations,tolerance,upper);
			impVolVector.push_back(comm.doubleToString(implVol));
		}
		catch (const exception& e){
			impVolVector.push_back(comm.doubleToString(upper));
		}		
		
		double maturity = usCal.businessDaysBetween(today, expDate, true, true) / 252.0;
		DeltaVector.push_back(comm.doubleToString(bls.delta("call",U,strike_given,implVol,maturity,rfr,0)));
	}

	vector<vector<string>> outVector;
	vector<string> header;

	//creating the header
	header.push_back("DateVal");
	header.push_back("S");
	header.push_back("V");
	header.push_back("Delta");
	header.push_back("ImpliedVol");
	header.push_back("HE");
	header.push_back("Cumulative HE");
	header.push_back("PNL");
	//header.push_back("PNL(with hedge)");

	double temp = (mid_price[0] - atof(DeltaVector[0].c_str()) * stockPrice[0]);
	double cumTemp = 0, delta_t = (1 / 252.0), hedgeError = 0;

	for (int i = 0; i < impVolVector.size(); i++) {
		vector<string>datarow;
		cout << impVolVector[i] + "->" + DeltaVector[i] << endl;
		datarow.push_back(dateVal[i]);
		datarow.push_back(comm.doubleToString(stockPrice[i]));
		datarow.push_back(comm.doubleToString(mid_price[i]));
		datarow.push_back(DeltaVector[i]);
		datarow.push_back(impVolVector[i]);
		
		
		if (i > 0) {
			hedgeError = atof(DeltaVector[i - 1].c_str())*stockPrice[i] + temp*exp(interest[i-1] * delta_t) - mid_price[i];
			temp = atof(DeltaVector[i - 1].c_str())*stockPrice[i] + temp*exp(interest[i-1] * delta_t) - atof(DeltaVector[i].c_str())*stockPrice[i];
			cumTemp = cumTemp + hedgeError;
		}
		
		datarow.push_back(comm.doubleToString(hedgeError));
		datarow.push_back(comm.doubleToString(cumTemp));
		datarow.push_back(comm.doubleToString(mid_price[i] - mid_price[0]));
		//double pnlHedge = (mid_price[i] - stockPrice[i] * atof(DeltaVector[i].c_str())) + (mid_price[0] - stockPrice[0] * atof(DeltaVector[0].c_str()));
		//datarow.push_back(comm.doubleToString(pnlHedge));
		outVector.push_back(datarow);
	}

	comm.toCSV(outVector, header, "result.csv","./");
	
	cout << usCal.businessDaysBetween(initDate, expDate, 0, 0) << endl;
	cout << "Part-2 Done" << endl;
	cout << "*****************************End*******************************" << endl;
	
	string test;
	cin >> test;

	return 0;
}