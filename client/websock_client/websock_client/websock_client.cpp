#include <iostream>
#ifdef _WIN32
#pragma comment(lib, "ws2_32")
#include <WinSock2.h>
#endif
#include "client.h"

using namespace easywsclient;
using namespace std;

auto main() -> int
{
	INT rc;
	WSADATA wsaData;

	rc = WSAStartup(MAKEWORD(2, 2), &wsaData);
	if (rc)
	{
		printf("WSAStartup Failed.\n");
		return 1;
	}

	return 0;
}
