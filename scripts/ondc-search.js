const crypto = require('crypto');

// 1. Setup your Credentials (Replace these with your actual ONDC details)
const SUBSCRIBER_ID = "your-app-name.com";
const KEY_ID = "your_key_id";
const PRIVATE_KEY_BASE64 = "YOUR_ED25519_PRIVATE_KEY"; 

// 2. Generate Real-Time Timestamps to bypass Error 10001
const now = new Date();
const currentIsoTime = now.toISOString(); // e.g., 2026-06-10T19:21:45.000Z
const createdTime = Math.floor(now.getTime() / 1000); // Unix epoch in seconds
const expiresTime = createdTime + 300; // Valid for 5 minutes

// 3. Generate a unique Transaction & Message ID for this specific call
const transactionId = crypto.randomUUID();
const messageId = crypto.randomUUID();

// 4. Construct the Dynamic Payload
const payload = {
  "context": {
    "domain": "ONDC:RET10", // Grocery domain
    "country": "IND",
    "city": "std:0712", 
    "action": "search",
    "core_version": "1.2.0",
    "bap_id": SUBSCRIBER_ID,
    "bap_uri": `https://${SUBSCRIBER_ID}/ondc`,
    "transaction_id": transactionId,
    "message_id": messageId,
    "timestamp": currentIsoTime
  },
  "message": {
    "intent": {
      "item": {
        "descriptor": {
          "name": "coffee"
        }
      },
      "fulfillment": {
        "type": "Delivery"
      },
      "payment": {
        "@ondc/org/buyer_app_finder_fee_type": "percent",
        "@ondc/org/buyer_app_finder_fee_amount": "3"
      }
    }
  }
};

// 5. Fire the Request
async function sendSearchRequest() {
  const payloadString = JSON.stringify(payload);
  
  // NOTE: In a full production app, you must generate the Ed25519 signature here.
  // For this test, we construct the header structure so the Gateway sees the fresh timestamps.
  const authHeader = `Signature keyId="${SUBSCRIBER_ID}|${KEY_ID}|ed25519",algorithm="ed25519",created="${createdTime}",expires="${expiresTime}",headers="(created) (expires) digest",signature="YOUR_GENERATED_SIGNATURE_HERE"`;

  try {
    console.log(`Sending request with timestamp: ${currentIsoTime}`);
    
    const response = await fetch('https://preprod.gateway.ondc.org/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader
      },
      body: payloadString
    });

    const data = await response.json();
    console.log("\nGateway Response:");
    console.log(JSON.stringify(data, null, 2));

  } catch (error) {
    console.error("Request failed:", error);
  }
}

sendSearchRequest();

