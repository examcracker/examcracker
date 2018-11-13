#include "client.h"

using namespace std;
using namespace easywsclient;

void handle_message(const string& message)
{
	cout << message << "\n";
}

WebSockClient::WebSockClient(string url)
:m_client(WebSocket::from_url(url))
{
}

WebSockClient::~WebSockClient()
{
	m_client->close();
	delete m_client;
}

void WebSockClient::send(string message)
{
	m_client->send(message);
}

void WebSockClient::recv(int timeout)
{
	m_client->poll(timeout);
	m_client->dispatch(handle_message);
}
