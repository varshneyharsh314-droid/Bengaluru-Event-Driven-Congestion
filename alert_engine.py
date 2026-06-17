import time

class IncidentAlertEngine:
    """
    Backend Engine to construct high-priority alerts and dispatch simulated SMS notifications
    to the nearest police station commanding officers.
    """
    
    @staticmethod
    def generate_alert_message(event_type, priority, congestion, expected_delay, police_needed, barricades, location_name, lat, lng):
        """
        Generates the standard structured alert text.
        """
        alert_text = (
            f"🚨 ALERT\n"
            f"Event Type: {event_type.upper()}\n"
            f"Priority: {priority.upper()}\n"
            f"Congestion: {congestion.upper()}\n"
            f"Expected Delay: {expected_delay} mins\n"
            f"Police Needed: {police_needed} officers\n"
            f"Barricades: {barricades} units\n"
            f"Location: {location_name} ({lat:.5f}, {lng:.5f})"
        )
        return alert_text

    @staticmethod
    def simulate_sms_dispatch(phone_number, alert_message):
        """
        Simulates the SMS API gateway transmission.
        Returns a dictionary containing the transmission metadata and log.
        """
        # Simulate quick API network handshake delay
        time.sleep(0.1)
        
        sms_log = {
            "status": "SENT",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "recipient_phone": phone_number,
            "gateway_message_id": f"MSG-SMS-{int(time.time())}",
            "characters_sent": len(alert_message),
            "payload": alert_message
        }
        
        return sms_log

if __name__ == "__main__":
    message = IncidentAlertEngine.generate_alert_message(
        event_type="unplanned",
        priority="High",
        congestion="High",
        expected_delay=90,
        police_needed=12,
        barricades=22,
        location_name="Silk Board Junction",
        lat=12.9176,
        lng=77.6246
    )
    print("Generated SMS Alert Text:")
    print(message)
    print("\nSimulated SMS Log:")
    log = IncidentAlertEngine.simulate_sms_dispatch("+91 94808-01824", message)
    for k, v in log.items():
        print(f"  {k}: {v}")
