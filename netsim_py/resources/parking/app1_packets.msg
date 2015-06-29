
cplusplus {{
#include "ApplicationPacket_m.h"
}}


packet ApplicationPacket;

enum AppMessageClass
{
	TELEMETRY_DISTANCE=1;
	TELEMETRY_TEMPERATURE=2;
	TELEMETRY_BATTERY=3;
};


packet Telemetry extends ApplicationPacket
{
	int appMessageClass @enum(AppMessageClass);
	string node;
	simtime_t m_time[];
	double measurement[];
};

