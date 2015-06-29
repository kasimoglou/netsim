
#ifndef __APP1_H
#define __APP1_H

#include "GenericOS.h"
#include "ApplicationPacket_m.h"
#include "app1_packets_m.h"


struct DataPublishTask : PeriodicTask
{
	DataBuffer* dataBuffer;
	int messageClass;

	DataPublishTask(GenericOS* __OS) : AppModule(__OS), PeriodicTask(__OS) {}

	void task();
};


struct BatteryReadTask : PeriodicTask, DataBuffer
{
	BatteryReadTask(GenericOS* __OS) :
		AppModule(__OS),
		PeriodicTask(__OS),
		DataBuffer(__OS) {}

	void task();	
};


/*
	Forwarding nodes only publish battery level.
 */
struct ParkingForward : GenericOS
{
	DataBuffer Battery;
	BatteryReadTask readBattery;
	DataPublishTask publishBattery;

	ParkingForward() : 
		Battery(this),
		readBattery(this),
		publishBattery(this)
		{}

	// methods
    void startup();

};

Define_Module(ParkingForward);



struct ParkingSensors : ParkingForward
{

	// measurement buffers
	SensorBuffer Temperature, Distance;
	SensorReadTask readTemperature, readDistance;
	DataPublishTask publishTemperature, publishDistance;

	ParkingSensors() :
		Temperature(this), Distance(this),
		readTemperature(this), readDistance(this),
		publishTemperature(this), publishDistance(this)
		{}

	// methods
    void startup();
    void finishSpecific();
};

Define_Module(ParkingSensors);


struct ParkingCollector : GenericOS
{
	inline int getMessageClass(ApplicationPacket *packet) {
		Telemetry* tmsg = check_and_cast<Telemetry*>(packet);

		return tmsg->getAppMessageClass();
	}

	void collect_data(ApplicationPacket* packet, const char* source, double rssi, double lqi);

    void startup();

};

Define_Module(ParkingCollector);


#endif