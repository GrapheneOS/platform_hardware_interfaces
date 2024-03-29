/*
 * Copyright (C) 2021 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package android.hardware.contexthub;

@VintfStability
parcelable ContextHubMessage {
    /** The unique identifier of the nanoapp. */
    long nanoappId;

    /**
     * The identifier of the host client that is sending/receiving this message.
     *
     * There are two reserved values of the host endpoint that has a specific meaning:
     * 1) BROADCAST = 0xFFFF: see CHRE_HOST_ENDPOINT_BROADCAST in
     *    system/chre/chre_api/include/chre_api/chre/event.h for details.
     * 2) UNSPECIFIED = 0xFFFE: see CHRE_HOST_ENDPOINT_UNSPECIFIED in
     *    system/chre/chre_api/include/chre_api/chre/event.h for details.
     */
    char hostEndPoint;

    /**
     * The type of this message payload, defined by the communication endpoints (i.e.
     * either the nanoapp or the host endpoint). This value can be used to distinguish
     * the handling of messageBody (e.g. for decoding).
     */
    int messageType;

    /** The payload containing the message. */
    byte[] messageBody;

    /**
     * The list of Android permissions held by the sending nanoapp at the time
     * the message was sent.
     *
     * The framework MUST drop messages to host apps that don't have a superset
     * of the permissions that the sending nanoapp is using.
     */
    String[] permissions;

    /**
     * Whether the message is reliable.
     *
     * For reliable messages, the receiver is expected to acknowledge the reception of
     * the message by sending a message delivery status back to the sender. Acknowledgment of
     * the message must be returned within 1 second.
     *
     * For reliable messages sent by the host, the Context Hub invokes
     * IContextHubCallback#handleMessageDeliveryStatus to report the status.
     *
     * For reliable messages sent by the Context Hub, the host calls
     * IContextHub#sendMessageDeliveryStatusToHub to report the status.
     */
    boolean isReliable;

    /**
     * The sequence number for a reliable message. For less than 2^32 messages, each message sent
     * from a Context Hub will have a unique sequence number generated by the Context Hub, and the
     * sequence numbers are guaranteed to not be reused for unacknowledged messages. For messages
     * sent to the Context Hub, sequence numbers are only guaranteed to be unique within the scope
     * of a given hostEndPoint. The sequence number may be reused if more than 2^32 messages are
     * sent, due to the size limit of int.
     *
     * The sequence number is used only for reliable messages. There is no guarantee of strict
     * ordering of messages. The recipient may receive messages with gaps between the sequence
     * numbers. This is not an indication of a missed message.
     *
     * See isReliable for more information.
     */
    int messageSequenceNumber;
}
