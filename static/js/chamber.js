// Context Data
const chamberId = JSON.parse(document.getElementById("chamber-id").textContent);
const chambername = JSON.parse(document.getElementById("chambername").textContent);
const isDebug = JSON.parse(document.getElementById("is_debug").textContent);
const username = JSON.parse(document.getElementById("username").textContent);


// Function to establish WebSocket connection
function connectWebSocket(){
    // const protocol = isDebug? "wss://" : "wss://";
    const protocol = "wss://";
    const chatSocket = new WebSocket(
        protocol + window.location.host + "/ws/chamber/" + chamberId + "/"
    );

    chatSocket.onopen = function(e) {
        console.log("connected")
    }

    let activeUserCount;

    chatSocket.onmessage = function(e){
        const data = JSON.parse(e.data);

        if (data.type === "chat.active") {
            activeUserCount = `online users: ${data.content}`;
            document.getElementById("active-status").textContent = activeUserCount;
        }
        else if (data.type === "chat.typing") {

            if (data.content && data.username === username) {
                document.getElementById("active-status").textContent = data.content;
            }
            else{
                document.getElementById("active-status").textContent = activeUserCount; 
            }
        }
    }

    chatSocket.onclose = function(e){
        console.error("Chat socket closed unexpectedly.");
    };

    let inputId = document.getElementById("message-input");
    let isMessageSent = false
    inputId.focus();
    inputId.addEventListener("input", function(){
        if (!isMessageSent) {
            chatSocket.send(JSON.stringify({"message": "typing", "message_type": "typing"}));
            isMessageSent = true;
        }
    });
    inputId.addEventListener("blur", function(){
        chatSocket.send(JSON.stringify({"message": "not_typing", "message_type": "typing"}));
        isMessageSent = false;
    });

};

connectWebSocket();







// const chatId = JSON.parse(document.getElementById("chat-id").textContent);
// const username = JSON.parse(document.getElementById("username").textContent);
// const otherUsername = JSON.parse(document.getElementById("other_username").textContent);
// const otherUserStatus = JSON.parse(document.getElementById("other_user_status").textContent);
// const isDebug = JSON.parse(document.getElementById("is_debug").textContent);

// Function to establish WebSocket connection
// function connectWebSocket() { 
//     const protocol = isDebug? "ws://" : "wss://";
//     const chatSocket = new WebSocket(
//         protocol + window.location.host + "/ws/chat/" + chatId + "/"
//     );
    

    // // Actions when message is received from room group
    // chatSocket.onmessage = function(e) {
    //     const data = JSON.parse(e.data);
    //     if (data.type === "chat.status") {
    //         if (data.username === otherUsername) {
    //             document.querySelectorAll(".status, .online").forEach(function(e) {
    //                 e.style.backgroundColor = data.content === "online" ? "#72d33d" : "rgb(169, 56, 56)";
    //             });
    //         }
    //     }
    //     else if (data.type === "chat.typing") {
    //         if (data.username === otherUsername) {
    //             document.querySelector("#chat-header").innerHTML = (data.content);
    //         }
    //     }
    //     else if (data.type === "chat.message") {
    //         createMessageBubble(data);
    //     }
    //     else if (data.type === "chat.reply") {
    //         createReplyBubble(data);
    //     }
    //     else if (data.type === "chat.audio") {
    //         createAudioBubble(data);
    //     }
    // };

    // chatSocket.onclose = function(e) {
    //     console.error("Chat socket closed unexpectedly.");
    //     setTimeout(connectWebSocket, 5000);
    // };

    // document.querySelector("#message-input").onkeyup = function(e) {
    //     if (e.key === "Enter") {
    //         sendMessage();
    //     }
    // };

    // document.querySelector("#submit").onclick = function(e) {
    //     sendMessage();
    // };

    // // Activates the input field for user to begin/resume typing
    // document.querySelector("#message-input").focus();

    // document.querySelector("#message-input").addEventListener("input", isTyping);
    // document.querySelector("#message-input").addEventListener("blur", isDormant);

    // // Scrolls to last chat message
    // scrollToBottom();

    // // Scrolls to replied message
    // scrollToBubble();
    
    // // Retrieves all chat bubbles and calls the drag function on individual bubbles
    // const bubbles = document.querySelectorAll(".my-bubble, .your-bubble");
    // bubbles.forEach(initiailizeDraggable);  

    // // Audio playback
    // document.querySelector("#chat-log").addEventListener("click", handleAudioPlayback);

    // // Audio Recording Setup
    // let mediaRecorder;
    // let audioChunks = []; // audio chunks will be appended here
    // const chunkSize = 1024 * 1024; // sets the chunk size to 1mb per chunk
    // let chunkIndex = 0; // increases as chunks are being appended to audiochunks

    // document.getElementById("record-stop").addEventListener("click", async () => {
    //     const recordButton = document.getElementById("record-stop");
    //     const icon = recordButton.querySelector(".icon");

    //     if (recordButton.classList.contains("recording")) {
    //         mediaRecorder.stop();
    //         recordButton.classList.remove("recording");
    //         icon.textContent = "🎤"; // Record icon
    //     } 
    //     else {
    //         try {
    //             // Grant access to device microphone. For camera, use { video: true }.
    //             const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    //             mediaRecorder = new MediaRecorder(stream); // MediaRecorder is a built-in JS API to record audio/video
    //             mediaRecorder.start(200); // Fires `dataavailable` event every 200 milliseconds
    
    //             mediaRecorder.addEventListener("dataavailable", event => {
    //                 audioChunks.push(event.data);
    //             });
    
    //             mediaRecorder.addEventListener("stop", async () => {
    //                 const audioBlob = new Blob(audioChunks);
    //                 audioChunks = []; // Resets for future recordings
    
    //                 // Send audio message via websocket as binary data (and any other message)
    //                 if (bubbleSelected === null) {
    //                     let messageData = JSON.stringify({
    //                         "type": "audio"
    //                     });
    //                     let messageBlob = new Blob([messageData], { type: "application/json" });
    //                     let delimiter = new Blob(["<delimiter>"], { type: "text/plain" }); // Adding a delimiter
    //                     let combinedBlob = new Blob([messageBlob, delimiter, audioBlob]);
    //                     chatSocket.send(combinedBlob);
    //                 }
    //                 else {
    //                     const previousMessageId = bubbleSelected.querySelector("#pentagon").innerText;
    //                     let messageData = JSON.stringify({
    //                         "previous_message_id": previousMessageId,
    //                         "type": "reply"
    //                     });
    //                     let messageBlob = new Blob([messageData], { type: "application/json" });
    //                     let delimiter = new Blob(["<delimiter>"], { type: "text/plain" }); // Adding a delimiter
    //                     let combinedBlob = new Blob([messageBlob, delimiter, audioBlob]);
    //                     chatSocket.send(combinedBlob);
    //                     bubbleSelected.style.transform = `translate(0)`;
    //                     const bubbleCloseButton = bubbleSelected.querySelector(".close-btn");
    //                     bubbleSelected.removeChild(bubbleCloseButton);
    //                     bubbleSelected = null;
    //                 }
    //             });
    
    //             // Update button text and state
    //             recordButton.classList.add("recording");
    //             icon.textContent = "⏹️"; // Stop icon
    //         } catch (err) {
    //             console.error("Error accessing media devices.", err);
    //         }
    //     }
    // });


    // // Handles loading of previous messages (paginated)
    // document.getElementById("previous-button").addEventListener("click", function() {
    //     loadMessages(this.getAttribute("data-url"), true);
    // });

    // function loadMessages(url, prepend = false) {
    //     if (!url) return;

    //     fetch(url, {
    //         headers: {
    //             "Accept": "application/json"
    //         }
    //     })
    //     .then(response => {
    //         if (!response.ok) {
    //             throw new Error("Network response was not ok.");
    //         }
    //         return response.json();
    //     })
    //     .then(data => {
    //         const chatLog = document.querySelector("#chat-log");

    //         data.results.forEach(message => {
    //             const messageDiv = document.createElement("div");
    //             messageDiv.className = message.sender === username ? "my-bubble" : "your-bubble";
    //             messageDiv.id = `message-${message.id}`;
    //             messageDiv.innerHTML = `
    //             <div class="${message.message_type === 'AUD' ? 'audio-message' : ''}">
    //             ${message.is_reply ? `
    //                 <div class="reply" data-reply-to="${message.previous_message_id}">
    //                     <span class="broker">${message.previous_sender}</span>
    //                     <span class="bank">${message.previous_content}${message.previous_content === 'AUDIO' ? '&#9658;' : ''}</span>
    //                     <p hidden>${message.previous_message_id}</p>
    //                 </div>
    //             ` : ''}
    //             ${message.message_type === 'AUD' ? `
    //                 <div class="purple">
    //                     <button class="play-button">&#9658;</button>
    //                     <div class="progress-bar">
    //                         <div class="progress"></div>
    //                     </div>
    //                     <span class="audio-duration">00:00</span>
    //                 </div>
    //                 <audio hidden>
    //                     <source src="${message.content}" type="audio/webm">
    //                 </audio>
    //             ` : `<span>${message.content}</span><br>`}
    //             <small>${message.time}</small>
    //             <p id="pentagon" hidden>${message.id}</p>
    //             </div>
    //         `;

    //             if (prepend) {
    //                 chatLog.insertBefore(messageDiv, chatLog.firstChild); // Prepend to top
    //             }
    //             else {
    //                 chatLog.appendChild(messageDiv); // Append to bottom
    //             }

    //             initiailizeDraggable(messageDiv);
    //             // scrollToBottom();
    //             scrollToBubble();
    //         });

    //         document.getElementById("previous-button").hidden = !data.previous;
    //         document.getElementById("previous-button").setAttribute("data-url", data.previous);

    //         if (!prepend) {
    //             scrollToBottom();
    //         }
    //     })
    //     .catch(error => console.error("Error loading messages:", error));
    // }



    // let isMessageSent = false // Prevents sending messages for each character typed

    // // Function to handle typing status
    // function isTyping() {
    //     if (!isMessageSent) {
    //         chatSocket.send(JSON.stringify({"message": "typing", "type": "typing"}));
    //         isMessageSent = true; // Ensures message is sent only once
    //     }
    // }

    // // Function to handle dormant status
    // function isDormant() {
    //     chatSocket.send(JSON.stringify({"message": "not_typing", "type": "typing"}));
    //     isMessageSent = false;
    // }

    // // Function to handle sending messages
    // function sendMessage() {
    //     const messageInputDom = document.querySelector("#message-input");
    //     const message = messageInputDom.value;

    //     // Send the message from websocket client to the consumer (normal message if no bubble is dragged else reply)
    //     if (bubbleSelected === null) {
    //         chatSocket.send(JSON.stringify({"message": message, "type": "message"}));
    //     } else {
    //         const previousMessageId = bubbleSelected.querySelector("#pentagon").innerText;
    //         chatSocket.send(JSON.stringify({"message": message, "previous_message_id": previousMessageId, "type": "reply"}));
    //         bubbleSelected.style.transform = `translate(0)`;
    //         const bubbleCloseButton = bubbleSelected.querySelector(".close-btn");
    //         bubbleSelected.removeChild(bubbleCloseButton);
    //         bubbleSelected = null;
    //     }

    //     messageInputDom.value = "";
    //     messageInputDom.focus();
    // }

    // // Function to create a new message bubble
    // function createMessageBubble(data) {
    //     var messageDiv = document.createElement("div");
    //     var innerMessageDiv = document.createElement("div");
    //     messageDiv.className = data.sender === username ? "my-bubble" : "your-bubble";
    //     messageDiv.id = `message-${data.id}`;
    //     innerMessageDiv.innerHTML = `
    //         <span>${data.content}</span><br>
    //         <small>${data.time}</small>
    //         <p id='pentagon' hidden>${data.id}</p>
    //     `;
    //     messageDiv.appendChild(innerMessageDiv);
    //     document.querySelector("#chat-log").appendChild(messageDiv);
    //     initiailizeDraggable(messageDiv);
    //     scrollToBottom();
    // }

    // // Function to create a reply bubble
    // function createReplyBubble(data) {
    //     var replyDiv = document.createElement("div");
    //     replyDiv.className = data.sender === username ? "my-bubble" : "your-bubble";
    //     replyDiv.id = `message-${data.id}`;
    //     var innerReplyDiv = document.createElement("div");
    //     var replyContentDiv = document.createElement("div");
    //     replyContentDiv.className = "reply";
    //     replyContentDiv.setAttribute("data-reply-to", data.previous_message_id);
    //     // Create the content for the previous message
    //     var previousContent = data.previous_content;
    //     if (previousContent === "AUDIO") {
    //         previousContent += " &#9658;";
    //     }
    //     replyContentDiv.innerHTML = `
    //         <span class='broker'>${data.previous_sender}</span>
    //         <span class='bank'>${previousContent}</span>
    //     `;
    //     innerReplyDiv.appendChild(replyContentDiv);
    //     if (data.reply_format === "audio") {
    //         innerReplyDiv.className = "audio-message";
    //         const audioUrl = `data:audio/wav;base64,${data.content}`;
    //         innerReplyDiv.innerHTML += `
    //             <div class="purple">
    //                 <button class="play-button">&#9658;</button>
    //                 <div class="progress-bar">
    //                     <div class="progress"></div>
    //                 </div>
    //                 <span class="audio-duration">00:00</span>
    //             </div>
    //             <audio hidden src="${audioUrl}"></audio>
    //             <small>${data.time}</small>
    //             <p id="pentagon" hidden>${data.id}</p>
    //         `;
    //     }
    //     else {
    //         innerReplyDiv.innerHTML += `
    //             <br><span>${data.content}</span><br>
    //             <small>${data.time}</small>
    //             <p id='pentagon' hidden>${data.id}</p>
    //         `;
    //     }
    //     replyDiv.appendChild(innerReplyDiv);
    //     document.querySelector("#chat-log").appendChild(replyDiv);
    //     initiailizeDraggable(replyDiv);
    //     scrollToBubble();
    //     scrollToBottom();
    // }

    // // Function to create an audio message bubble
    // function createAudioBubble(data) {
    //     const audioMessageDiv = document.createElement("div");
    //     audioMessageDiv.className = data.sender === username ? "my-bubble" : "your-bubble";
    //     audioMessageDiv.id = `message-${data.id}`;
    //     const innerAudioMessageDiv = document.createElement("div");
    //     innerAudioMessageDiv.className = "audio-message";
    //     const audioUrl = `data:audio/wav;base64,${data.content}`;
    //     innerAudioMessageDiv.innerHTML = `
    //         <div class="purple">
    //             <button class="play-button">&#9658;</button>
    //             <div class="progress-bar">
    //                 <div class="progress"></div>
    //             </div>
    //             <span class="audio-duration">00:00</span>
    //         </div>
    //         <audio hidden src="${audioUrl}"></audio>
    //         <small>${data.time}</small>
    //         <p id="pentagon" hidden>${data.id}</p>
    //     `;
    //     audioMessageDiv.appendChild(innerAudioMessageDiv);
    //     document.querySelector("#chat-log").appendChild(audioMessageDiv);
    //     initiailizeDraggable(audioMessageDiv);
    //     scrollToBottom();
    // }

    // let bubbleSelected = null;  

    // // Functionality for making chat bubbles draggable
    // function initiailizeDraggable(bubble) {
    //     const maxDragDistance = 50;

    //     // Adds a button to dragged bubbles to enable reset on click
    //     const closeButton = document.createElement("button");
    //     closeButton.classList.add("close-btn");
    //     closeButton.innerText = "x";

    //     // This resets dragged bubbles on click
    //     closeButton.addEventListener("click", () => {
    //         bubble.style.transform = `translate(0)`;
    //         bubble.removeChild(closeButton);
    //         bubbleSelected = null;
    //     });

    //     bubble.addEventListener("mousedown", (e) => {
    //         let startX = e.clientX;
            
    //         function onMouseMove(event) {
    //             // Resets previous bubbles when a new bubble is dragged
    //             if (bubbleSelected && bubbleSelected !== bubble) {
    //                 bubbleSelected.style.transform = `translate(0)`;
    //                 const bubbleCloseButton = bubbleSelected.querySelector(".close-btn");
    //                 bubbleSelected.removeChild(bubbleCloseButton);
    //                 bubbleSelected = null;
    //             }

    //             let moveX = event.clientX - startX;
    //             let moveY = startX - event.clientX;

    //             // Current user's bubbles can only be dragged to the left
    //             if (moveX < 0 && Math.abs(moveX) < maxDragDistance) {
    //                 if (bubble.className == "my-bubble") {
    //                     bubble.style.transform = `translate(${moveX}px)`;
    //                     bubble.appendChild(closeButton);
    //                     bubbleSelected = bubble;
    //                     document.querySelector("#message-input").focus();
    //                 }
                        
    //             };

    //             // Other users' bubbles can only be dragged to the right
    //             if (moveY < 0 && Math.abs(moveY) < maxDragDistance) {
    //                 if (bubble.className == "your-bubble") {
    //                     bubble.style.transform = `translate(${-moveY}px)`;
    //                     bubble.appendChild(closeButton);
    //                     bubbleSelected = bubble;
    //                     document.querySelector("#message-input").focus();
    //                 }
    //             };
    //         }
                

    //         function onMouseUp() {
    //             document.removeEventListener("mousemove", onMouseMove);
    //             document.removeEventListener("mouseup", onMouseUp);
    //         }

    //         document.addEventListener("mousemove", onMouseMove);
    //         document.addEventListener("mouseup", onMouseUp);
    //     });
    // };

    // // Function to scroll to the bottom of the chat log
    // function scrollToBottom() {
    //     let objDiv = document.querySelector("#chat-log");
    //     objDiv.scrollTop = objDiv.scrollHeight;
    // }

    // // Function to scroll to original message when reply bubbles are clicked
    // function scrollToBubble() {
    //     const replyBubbles = document.querySelectorAll(".reply");
    //     replyBubbles.forEach(bubble => {
    //         bubble.addEventListener("click", () => {
    //             const replyToId = bubble.getAttribute("data-reply-to");
    //             const originalMessage = document.querySelector(`#message-${replyToId}`);
    //             if (originalMessage) {
    //                 originalMessage.scrollIntoView({ behavior: "smooth" });
    //             }
    //         });
    //     });
    // }

    // // Function to handle audio playback
    // function handleAudioPlayback(e) {
    //     if (e.target.classList.contains("play-button")) {
    //         const audioContainer = e.target.closest(".audio-message");
    //         const audio = audioContainer.querySelector("audio");
    //         const progressBar = audioContainer.querySelector(".progress");
    //         const durationDisplay = audioContainer.querySelector(".audio-duration");

    //         if (audio.paused) {
    //             audio.play();
    //             e.target.innerHTML = "&#10074;&#10074;";
    //         } else {
    //             audio.pause();
    //             e.target.innerHTML = "&#9658;";
    //         }

    //         audio.ontimeupdate = function() {
    //             const progressPercent = (audio.currentTime / audio.duration) * 100;
    //             progressBar.style.width = `${progressPercent}%`;

    //             const minutes = Math.floor(audio.currentTime / 60);
    //             const seconds = Math.floor(audio.currentTime % 60);
    //             durationDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    //         };

    //         audio.onended = function() {
    //             e.target.innerHTML = "&#9658;";
    //             progressBar.style.width = "0";
    //             durationDisplay.textContent = "00:00";
    //         };
    //     }
    // }

// };

// connectWebSocket();