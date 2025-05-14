import streamlit as st
import database as db
import sqlite3 as sql
from datetime import datetime

class Appointment:
    def __init__(self):
        self.conn, self.cursor = db.connection()

    def add_appointment(self):
        # Create form for appointment details
        with st.form("add_appointment_form"):
            st.subheader("Patient Information")
            name = st.text_input("Patient Name")
            age = st.number_input("Age", min_value=0, max_value=120)
            health_problem = st.text_area("Health Problem/Issue")
            
            st.subheader("Appointment Details")
            # Get all doctors for selection
            self.cursor.execute("SELECT id, name FROM doctor_record")
            doctors = self.cursor.fetchall()
            doctor_options = {f"{d[1]} (ID: {d[0]})": d[0] for d in doctors}

            if not doctors:
                st.error("No doctors available. Please add doctors first.")
                return

            doctor = st.selectbox("Select Doctor", options=list(doctor_options.keys()))
            appointment_date = st.date_input("Appointment Date")
            appointment_time = st.time_input("Appointment Time")
            
            if st.form_submit_button("Add Appointment"):
                try:
                    if not name or not health_problem:
                        st.error("Please fill in all required fields")
                        return
                        
                    doctor_id = doctor_options[doctor]
                    appointment_datetime = datetime.combine(appointment_date, appointment_time)
                    
                    # Generate appointment ID
                    appointment_id = f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    self.cursor.execute("""
                        INSERT INTO appointments (
                            appointment_id, patient_name, patient_age, health_problem,
                            doctor_id, appointment_datetime
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (appointment_id, name, age, health_problem, 
                          doctor_id, appointment_datetime))
                    
                    self.conn.commit()
                    st.success("Appointment added successfully!")
                except sql.Error as e:
                    st.error(f"Error adding appointment: {e}")

    def update_appointment(self):
        # Get all appointments
        self.cursor.execute("""
            SELECT a.appointment_id, a.patient_name, a.patient_age, a.health_problem,
                   d.name as doctor_name, a.appointment_datetime
            FROM appointments a
            JOIN doctor_record d ON a.doctor_id = d.id
        """)
        appointments = self.cursor.fetchall()
        
        if not appointments:
            st.error("No appointments found.")
            return

        appointment_options = {
            f"Appointment {a[0]} - {a[1]} with Dr. {a[4]} on {a[5]}": a[0] 
            for a in appointments
        }

        selected_appointment = st.selectbox("Select Appointment to Update", 
                                          options=list(appointment_options.keys()))
        
        if selected_appointment:
            appointment_id = appointment_options[selected_appointment]
            
            # Get current appointment details
            self.cursor.execute("""
                SELECT * FROM appointments WHERE appointment_id = ?
            """, (appointment_id,))
            current_appointment = self.cursor.fetchone()

            with st.form("update_appointment_form"):
                st.subheader("Patient Information")
                new_name = st.text_input("Patient Name", value=current_appointment[1])
                new_age = st.number_input("Age", min_value=0, max_value=120, 
                                        value=current_appointment[2])
                new_health_problem = st.text_area("Health Problem/Issue", 
                                                value=current_appointment[3])
                
                st.subheader("Appointment Details")
                new_date = st.date_input("New Appointment Date", 
                                       value=datetime.strptime(current_appointment[5], 
                                                             "%Y-%m-%d %H:%M:%S").date())
                new_time = st.time_input("New Appointment Time", 
                                       value=datetime.strptime(current_appointment[5], 
                                                             "%Y-%m-%d %H:%M:%S").time())
                
                if st.form_submit_button("Update Appointment"):
                    try:
                        new_datetime = datetime.combine(new_date, new_time)
                        self.cursor.execute("""
                            UPDATE appointments 
                            SET patient_name = ?, patient_age = ?, health_problem = ?,
                                appointment_datetime = ?
                            WHERE appointment_id = ?
                        """, (new_name, new_age, new_health_problem, 
                              new_datetime, appointment_id))
                        
                        self.conn.commit()
                        st.success("Appointment updated successfully!")
                    except sql.Error as e:
                        st.error(f"Error updating appointment: {e}")

    def delete_appointment(self):
        # Get all appointments
        self.cursor.execute("""
            SELECT a.appointment_id, a.patient_name, a.patient_age, a.health_problem,
                   d.name as doctor_name, a.appointment_datetime
            FROM appointments a
            JOIN doctor_record d ON a.doctor_id = d.id
        """)
        appointments = self.cursor.fetchall()
        
        if not appointments:
            st.error("No appointments found.")
            return

        appointment_options = {
            f"Appointment {a[0]} - {a[1]} with Dr. {a[4]} on {a[5]}": a[0] 
            for a in appointments
        }

        selected_appointment = st.selectbox("Select Appointment to Delete", 
                                          options=list(appointment_options.keys()))
        
        if selected_appointment and st.button("Delete Appointment"):
            try:
                appointment_id = appointment_options[selected_appointment]
                self.cursor.execute("DELETE FROM appointments WHERE appointment_id = ?", 
                                  (appointment_id,))
                self.conn.commit()
                st.success("Appointment deleted successfully!")
            except sql.Error as e:
                st.error(f"Error deleting appointment: {e}")

    def show_all_appointments(self):
        self.cursor.execute("""
            SELECT a.appointment_id, a.patient_name, a.patient_age, a.health_problem,
                   d.name as doctor_name, a.appointment_datetime
            FROM appointments a
            JOIN doctor_record d ON a.doctor_id = d.id
            ORDER BY a.appointment_datetime
        """)
        appointments = self.cursor.fetchall()
        
        if appointments:
            st.subheader("All Appointments")
            for appointment in appointments:
                st.write(f"""
                    **Appointment ID:** {appointment[0]}  
                    **Patient Name:** {appointment[1]}  
                    **Age:** {appointment[2]}  
                    **Health Problem:** {appointment[3]}  
                    **Doctor:** {appointment[4]}  
                    **Date & Time:** {appointment[5]}
                    ---
                """)
        else:
            st.info("No appointments found.")

    def appointments_by_patient(self):
        # Get all patients from appointments
        self.cursor.execute("SELECT DISTINCT patient_name FROM appointments")
        patients = self.cursor.fetchall()
        
        if not patients:
            st.error("No patients found.")
            return

        patient_options = [p[0] for p in patients]
        selected_patient = st.selectbox("Select Patient", options=patient_options)
        
        if selected_patient:
            self.cursor.execute("""
                SELECT a.appointment_id, a.patient_age, a.health_problem,
                       d.name as doctor_name, a.appointment_datetime
                FROM appointments a
                JOIN doctor_record d ON a.doctor_id = d.id
                WHERE a.patient_name = ?
                ORDER BY a.appointment_datetime
            """, (selected_patient,))
            
            appointments = self.cursor.fetchall()
            
            if appointments:
                st.subheader(f"Appointments for {selected_patient}")
                for appointment in appointments:
                    st.write(f"""
                        **Appointment ID:** {appointment[0]}  
                        **Age:** {appointment[1]}  
                        **Health Problem:** {appointment[2]}  
                        **Doctor:** {appointment[3]}  
                        **Date & Time:** {appointment[4]}
                        ---
                    """)
            else:
                st.info(f"No appointments found for {selected_patient}.") 