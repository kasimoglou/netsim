//
// Generated file, do not edit! Created by opp_msgc 4.4 from src/node/mobilityManager/MobilityManagerMessage.msg.
//

#ifndef _MOBILITYMANAGERMESSAGE_M_H_
#define _MOBILITYMANAGERMESSAGE_M_H_

#include <omnetpp.h>

// opp_msgc version check
#define MSGC_VERSION 0x0404
#if (MSGC_VERSION!=OMNETPP_VERSION)
#    error Version mismatch! Probably this file was generated by an earlier version of opp_msgc: 'make clean' should help.
#endif



/**
 * Enum generated from <tt>src/node/mobilityManager/MobilityManagerMessage.msg</tt> by opp_msgc.
 * <pre>
 * enum MobilityManagerMessageType {
 * 	MOBILITY_PERIODIC = 1;
 * }
 * </pre>
 */
enum MobilityManagerMessageType {
    MOBILITY_PERIODIC = 1
};

/**
 * Class generated from <tt>src/node/mobilityManager/MobilityManagerMessage.msg</tt> by opp_msgc.
 * <pre>
 * message MobilityManagerMessage {
 * }
 * </pre>
 */
class MobilityManagerMessage : public ::cMessage
{
  protected:

  private:
    void copy(const MobilityManagerMessage& other);

  protected:
    // protected and unimplemented operator==(), to prevent accidental usage
    bool operator==(const MobilityManagerMessage&);

  public:
    MobilityManagerMessage(const char *name=NULL, int kind=0);
    MobilityManagerMessage(const MobilityManagerMessage& other);
    virtual ~MobilityManagerMessage();
    MobilityManagerMessage& operator=(const MobilityManagerMessage& other);
    virtual MobilityManagerMessage *dup() const {return new MobilityManagerMessage(*this);}
    virtual void parsimPack(cCommBuffer *b);
    virtual void parsimUnpack(cCommBuffer *b);

    // field getter/setter methods
};

inline void doPacking(cCommBuffer *b, MobilityManagerMessage& obj) {obj.parsimPack(b);}
inline void doUnpacking(cCommBuffer *b, MobilityManagerMessage& obj) {obj.parsimUnpack(b);}


#endif // _MOBILITYMANAGERMESSAGE_M_H_