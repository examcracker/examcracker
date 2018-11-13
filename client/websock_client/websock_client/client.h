#pragma once
#include <iostream>
#include "easywsclient.hpp"

class WebSockClient
{
public:
	WebSockClient(std::string url) throw();
	virtual ~WebSockClient() throw();

	void send(std::string message);
	void recv(int timeout = 0);

private:
	easywsclient::WebSocket::pointer m_client;
};