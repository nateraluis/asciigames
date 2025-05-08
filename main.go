package main

import (
	"github.com/gliderlabs/ssh"
	"github.com/creack/pty"
	"io"
	"log"
	"os"
	"os/exec"
	"syscall"
	"unsafe"
	"time"
)


func main() {
	ssh.Handle(func(s ssh.Session) {
		start := time.Now()
		defer logConnection(s, start)
		ptyReq, winCh, hasPty := s.Pty()
		if !hasPty {
			io.WriteString(s, "A terminal is required to play this game.\n")
			s.Exit(1)
			return
		}

		cmd := exec.Command("python3", "home/ubuntu/asciigames/flight_sim.py")
		cmd.Env = append(os.Environ(), "TERM="+ptyReq.Term)

		ptmx, err := pty.Start(cmd)
		if err != nil {
			io.WriteString(s, "Error starting terminal: "+err.Error()+"\n")
			s.Exit(1)
			return
		}
		defer func() { _ = ptmx.Close() }()

		// Set initial size
		_ = pty.Setsize(ptmx, &pty.Winsize{
			Rows: uint16(ptyReq.Window.Height),
			Cols: uint16(ptyReq.Window.Width),
		})

		// Watch window changes
		go func() {
			for win := range winCh {
				_ = pty.Setsize(ptmx, &pty.Winsize{
					Rows: uint16(win.Height),
					Cols: uint16(win.Width),
				})
			}
		}()

		if err := cmd.Run(); err != nil {
			io.WriteString(s, "Error: "+err.Error()+"\n")
		}
		
		// Pipe data
		go func() { _, _ = io.Copy(ptmx, s) }()
		_, _ = io.Copy(s, ptmx)
	})

	log.Println("Starting SSH server on port 22...")
	log.Fatal(ssh.ListenAndServe(":22", nil,
		ssh.HostKeyFile("/etc/ssh/ssh_host_rsa_key"),
	))
}

func setWinsize(pid int, w, h int) {
	ws := &struct {
		Height uint16
		Width  uint16
		x      uint16
		y      uint16
	}{uint16(h), uint16(w), 0, 0}

	syscall.Syscall(
		syscall.SYS_IOCTL,
		uintptr(pid),
		uintptr(syscall.TIOCSWINSZ),
		uintptr(unsafe.Pointer(ws)),
	)
}

func logConnection(s ssh.Session, start time.Time) {
	remote := s.RemoteAddr().String()
	end := time.Now()
	duration := end.Sub(start).Round(time.Second)

	entry := "[" + start.Format(time.RFC3339) + "] " +
	"IP: " + remote + 
	" | Duration: " + duration.String() + "\n"

	f, err := os.OpenFile("/home/ubuntu/asciigames/connections.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err == nil {
		defer f.Close()
		_, _ = f.WriteString(entry)
	}
}
