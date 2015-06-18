/**
 * @author Phil Levis <pal@cs.berkeley.edu>
 * @date August 12 2005
 */

import java.io.BufferedOutputStream;
import java.io.BufferedWriter;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;

import java.io.IOException;

import net.tinyos.message.*;
import net.tinyos.packet.*;
import net.tinyos.util.*;

/*  RssiMsg structure
 *  mid  /  fields[4]   / Crc
 *  1 b  /  4 x 1 b     / 1 b , b = byte
 */

// Improved Version add  ->  IVA
import java.util.concurrent.Semaphore;



public class TestSerial implements MessageListener {

  private static Semaphore sem;   // IVA

  static int packetNo; 
  static int no_id;
  static String fileName;
  static int virtual_id;

  private MoteIF moteIF;
  
  
  public void sendPackets() {

    int counter = 0;
    RssiMsg payload = new RssiMsg();

    try {        

         while (counter <= packetNo ) {
         
  	     payload.set_cmdid((short)no_id);     // Set cmdid {  20/ 21/ 22  }
             moteIF.send(0, payload);
             counter++;
             // IVA Starts
             try{
                sem.acquire();
             }catch(InterruptedException e){}
             //try {
             //   Thread.sleep(50);
             //}catch (InterruptedException exception) {}
             //try {Thread.sleep(1000);}      // Is it enough ? Maybe change it with semaphore Version
	     //catch (InterruptedException exception) {}
             // IVA Ends
         }      
    }catch (IOException exception) {
       System.err.println("Exception thrown when sending packets. Exiting.");
       System.err.println(exception);
    }

  }

  public void messageReceived(int to, Message message) {
      
    RssiMsg msg = (RssiMsg)message;
    System.out.println("TS: Received packet type " + msg.get_cmdid());
    System.out.println("TS: Received packet Rssi " + msg.getElement_fields(0));
    String rssidBm ;  
    try {
 
	  File file = new File(fileName); 
          FileWriter fw = new FileWriter( file.getAbsoluteFile() );
          BufferedWriter bw = new BufferedWriter( fw );
        
          if(msg.get_cmdid() == 20 || msg.get_cmdid() == 21){
              rssidBm = ( new Integer( msg.getElement_fields(0) -45 ).toString() ); // This transformation could be done in Mote Code
              bw.write( rssidBm );                                 
              //-System.out.println("TS: Writing to file  " + rssidBm );
          }else if(msg.get_cmdid() == 22){
              rssidBm = ( new Integer( msg.getElement_fields(0) ).toString() );
              bw.write( rssidBm );                                 
              //-System.out.println(" Ber(20)/Rssi(-45)  : " + rssidBm ); 
              rssidBm = ( new Integer( msg.getElement_fields(1) ).toString() );
              bw.write( rssidBm );                                 
              //-System.out.println(" Aer(20)            : " + rssidBm );
              rssidBm = ( new Integer( msg.getElement_fields(2) ).toString() );
              bw.write( rssidBm );                                 
              //-System.out.println(" Ber(21)            : " + rssidBm );
              rssidBm = ( new Integer( msg.getElement_fields(3) ).toString() );
              bw.write( rssidBm );                                 
              //-System.out.println(" Aer(21)            : " + rssidBm );
          }
          bw.close();
                      
    } catch (IOException e) {
	e.printStackTrace();
    }
        sem.release();    // IVA
  }
   
  public TestSerial(MoteIF moteIF) {
    this.moteIF = moteIF;
    this.moteIF.registerListener(new RssiMsg(), this);
    this.sem = new Semaphore(0);  // IVA
  }

  // Entry Point
  public static void main(String[] args) throws Exception {

     String source = null;
   
     if (args.length != 5) {
	 usage();
	 System.exit(1);
     }

     if (!args[0].equals("-comm")) {
        usage();
	System.exit(1);
     }
    
     source = args[1];
     virtual_id = Integer.parseInt(args[4]);
     fileName = "/home/gwho/myPipe";

     PhoenixSource phoenix;
     
     if (source == null) {
       phoenix = BuildSource.makePhoenix(PrintStreamMessenger.err);
       System.out.println("ARTEMIS 1");  
     }
     else {
       phoenix = BuildSource.makePhoenix(source, PrintStreamMessenger.err);
       System.out.println("ARTEMIS 2");
     }
     
     MoteIF mif = new MoteIF(phoenix);
     TestSerial serial = new TestSerial(mif);
     System.out.println("ARTEMIS " + args[2]);

     packetNo = Integer.parseInt(args[2]);
     no_id = Integer.parseInt(args[3]);
       
     serial.sendPackets();
     System.exit(0);     
  }

  // Utility Function
  private static void usage() {
    System.err.println("usage: TestSerial [-comm <source>] PacketNo-1 commandCode NodeId");
  }


}


