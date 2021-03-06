//
// Generated file, do not edit! Created by opp_msgc 4.4 from src/node/resourceManager/ResourceManagerMessage.msg.
//

#ifndef _RESOURCEMANAGERMESSAGE_M_H_
#define _RESOURCEMANAGERMESSAGE_M_H_

#include <omnetpp.h>

// opp_msgc version check
#define MSGC_VERSION 0x0404
#if (MSGC_VERSION!=OMNETPP_VERSION)
#    error Version mismatch! Probably this file was generated by an earlier version of opp_msgc: 'make clean' should help.
#endif



/**
 * Class generated from <tt>src/node/resourceManager/ResourceManagerMessage.msg</tt> by opp_msgc.
 * <pre>
 * message ResourceManagerMessage {
 * 	double powerConsumed;
 * }
 * </pre>
 */
class ResourceManagerMessage : public ::cMessage
{
  protected:
    double powerConsumed_var;

  private:
    void copy(const ResourceManagerMessage& other);

  protected:
    // protected and unimplemented operator==(), to prevent accidental usage
    bool operator==(const ResourceManagerMessage&);

  public:
    ResourceManagerMessage(const char *name=NULL, int kind=0);
    ResourceManagerMessage(const ResourceManagerMessage& other);
    virtual ~ResourceManagerMessage();
    ResourceManagerMessage& operator=(const ResourceManagerMessage& other);
    virtual ResourceManagerMessage *dup() const {return new ResourceManagerMessage(*this);}
    virtual void parsimPack(cCommBuffer *b);
    virtual void parsimUnpack(cCommBuffer *b);

    // field getter/setter methods
    virtual double getPowerConsumed() const;
    virtual void setPowerConsumed(double powerConsumed);
};

inline void doPacking(cCommBuffer *b, ResourceManagerMessage& obj) {obj.parsimPack(b);}
inline void doUnpacking(cCommBuffer *b, ResourceManagerMessage& obj) {obj.parsimUnpack(b);}


#endif // _RESOURCEMANAGERMESSAGE_M_H_
