package httpapi

import "net"

// newListener opens a TCP listener suitable for tests (port 0 picks a free
// port). The concrete net.Listener lets us read the bound address even when
// the configured port was 0.
func newListener(host string, port int) (net.Listener, error) {
	addr := host
	if port > 0 {
		addr = net.JoinHostPort(host, strconvI(port))
	}
	return net.Listen("tcp", addr)
}

// strconvI is a tiny indirection to avoid importing strconv at the top of
// this file (which is loaded by tests).
func strconvI(p int) string {
	const digits = "0123456789"
	if p == 0 {
		return "0"
	}
	neg := p < 0
	if neg {
		p = -p
	}
	var buf [20]byte
	i := len(buf)
	for p > 0 {
		i--
		buf[i] = digits[p%10]
		p /= 10
	}
	if neg {
		i--
		buf[i] = '-'
	}
	return string(buf[i:])
}
