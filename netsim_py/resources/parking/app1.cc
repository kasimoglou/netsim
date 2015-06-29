
#include <iostream>
#include <memory>
#include <functional>


#include "GenericOS.h"
#include "app1.h"

#include <cstdlib>

using namespace std;


// ----- SensorPublishTask

void DataPublishTask::task()
{
	// Create new message
	if (dataBuffer->size()==0)
		return;

	Telemetry* msg = new Telemetry("Telemetry package", APPLICATION_PACKET);

	msg->setSequenceNumber(OS->packetSequenceNumber ++);

	msg->setAppMessageClass(messageClass);

	msg->setMeasurementArraySize(dataBuffer->size());
	msg->setM_timeArraySize(dataBuffer->size());

	msg->setByteLength(8*dataBuffer->size());

	OS->collectOutput("NodeStatistics", "SentTelemetryPackets");
	OS->collectOutput("NodeStatistics", "SentTelemetrySamples", dataBuffer->size());

	for(size_t i=0;i<dataBuffer->size();i++) {
		msg->setM_time(i, dataBuffer->m_time[i]);
		msg->setMeasurement(i, dataBuffer->measurement[i]);
	}

	dataBuffer->clear();

	cerr << "Message sent" << endl;
	OS->send_message(msg, "7");
	//delete msg;
}


// ----- BatteryReadTask

void BatteryReadTask::task()
{
	double re = OS->resourceManager()->getSpentEnergy();
	record(re);
}


// ----- ParkingSensors

void ParkingForward::startup()
{
	GenericOS::startup();

	readBattery.period = 30.0;
	publishBattery.dataBuffer = & Battery;
	publishBattery.period = 120.0;

	readBattery.fired();
	publishBattery.fired();
	declareOutput("NodeStatistics");
}


void ParkingSensors::startup()
{
	ParkingForward::startup();

	Distance.sensorIndex = 0;
	Distance.sensorType = "Distance";
	readDistance.sensorBuffer = &Distance;
	readDistance.period = 30.0;
	publishDistance.dataBuffer = &Distance;
	publishDistance.period = 120.0;

	addSensorBuffer(&Distance);

	Temperature.sensorIndex = 1;
	Temperature.sensorType = "Temperature";
	readTemperature.sensorBuffer = &Temperature;
	readTemperature.period = 30.0;
	publishTemperature.dataBuffer = &Temperature;
	publishTemperature.period = 120.0;

	addSensorBuffer(&Temperature);

	readTemperature.fired();
	publishTemperature.fired();
	readDistance.fired();
	publishDistance.fired();

}

void ParkingCollector::startup()
{
	GenericOS::startup();
	addHandler(0, &ParkingCollector::collect_data, this);

	declareOutput("CollectorStatistics");
}

void ParkingCollector::collect_data(ApplicationPacket* packet, 
	const char* source, double rssi, double lqi)
{
	Telemetry* msg = check_and_cast<Telemetry*>(packet);

	cerr << "Node " << self << " received packet " << msg->getAppMessageClass() << " from " << source
		<< " RSSI=" << rssi << " LQI=" << lqi << endl;

	collectOutput("CollectorStatistics", atoi(source), "ReceivedMessage");
	collectOutput("CollectorStatistics", atoi(source), 
		"ReveivedSamples", msg->getMeasurementArraySize());

}


void ParkingSensors::finishSpecific()
{
	ParkingForward::finishSpecific();

}


