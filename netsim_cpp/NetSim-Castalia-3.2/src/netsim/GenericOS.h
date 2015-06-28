
#ifndef _GENERICOS_H_
#define _GENERICOS_H_

#include <typeinfo>
#include <string>
#include <vector>
#include <map>

#include <boost/function.hpp>
#include <boost/bind.hpp>

#include "VirtualApplication.h"
#include "ApplicationPacket_m.h"

using namespace std;

class GenericOS;

/**
	A simple base class holding a reference to a
	GenericOS object.
  */
struct AppModule
{
	GenericOS * OS;
	AppModule(GenericOS* __OS) : OS(__OS) {}
};


/*
	A base class for defining periodic tasks in the application logic.
 */
struct PeriodicTask : virtual AppModule
{
	int timer_id;
	simtime_t period;

	PeriodicTask(GenericOS* __OS);

	virtual void task() = 0;

	void fired();
};


/*
	A base class for collecting data measurements
 */
struct DataBuffer : virtual AppModule
{
	vector<double> measurement;
	vector<simtime_t> m_time;

	DataBuffer(GenericOS* __OS) : AppModule(__OS) {}

	virtual void record(double m);

	inline size_t size() const { return measurement.size(); }
	inline void clear() { 
		measurement.clear();
		m_time.clear();
	}
};


/*
	A base class for collecting measurements from sensors.
 */

struct SensorBuffer : DataBuffer
{

	int sensorIndex;
	string sensorType;

	SensorBuffer(GenericOS* __OS) 
	:
		AppModule(__OS),
		DataBuffer(__OS),
		sensorIndex(),
		sensorType() 
		{}

	virtual void request();
};



typedef boost::function< void (ApplicationPacket*, const char*, double, double) > MessageHandler;



/*
	A Generic OS module with a number of services for
	modular logic composition.
 */
class GenericOS : public VirtualApplication {

 public:
	// parameters and variables
	int priority;
	int packetHeaderOverhead;
	int constantDataPayload;
	int packetSequenceNumber;

	// the vector of periodic tasks
	vector<PeriodicTask*> periodicTasks;

	// Add a periodic task to the vecot of tasks and
	// return the timer id for it.
	// N.B. This is called from the periodic task constructor.
	int addPeriodicTask(PeriodicTask* task);

	// Map for sensor buffers
	map<int, SensorBuffer*> sensorBuffers;
	// Add a sensor handler for the specified physical measure
	void addSensorBuffer(SensorBuffer* sensorBuffer);


	// Map for message handlers
	map<int, MessageHandler> handlers;

	template <typename Cls>
	void addHandler( int msgClass,
		void ( Cls:: * member )(ApplicationPacket*,const char*,double,double),
		Cls* obj )
	{
		handlers[msgClass] = boost::bind(member, obj, _1, _2, _3, _4);
	}


	// Subclasses can redefine this to specialize handler calls
	virtual int getMessageClass(ApplicationPacket* packet) 
	{
		return 0;
	}

	//
	// Generic methods
	//

	void startup();
	void finishSpecific();

	void fromNetworkLayer(ApplicationPacket *, const char *, double, double);

	void timerFiredCallback(int);

	inline void requestSensorReading(int index) {
		VirtualApplication::requestSensorReading(index);
	}

	void initialize();

	inline void sendToNetwork(cPacket* p, const char* dest) {
		toNetworkLayer(p, dest);
	}

	void fireTimerAfter(int timer_id, simtime_t duration);

	void send_message(ApplicationPacket* packet, const char* dest);

	ResourceManager* resourceManager() const { return resMgrModule; }

};


inline void PeriodicTask::fired() {
	// call the task
	task();
	OS->fireTimerAfter(timer_id, period);
}



struct SensorReadTask : PeriodicTask
{
	SensorBuffer* sensorBuffer;

	SensorReadTask(GenericOS*);	

	virtual void task();
};





#endif

