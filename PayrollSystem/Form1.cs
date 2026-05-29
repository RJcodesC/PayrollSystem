using System;
using System.Windows.Forms;

namespace PayrollSystem
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            // Validation

            if (string.IsNullOrWhiteSpace(textBox1.Text))
            {
                MessageBox.Show("Enter contractor name.");
                return;
            }

            double hours;
            int dependents;

            if (!double.TryParse(textBox3.Text, out hours))
            {
                MessageBox.Show("Hours worked must be numeric.");
                return;
            }

            if (!int.TryParse(textBox2.Text, out dependents))
            {
                MessageBox.Show("Dependents must be numeric.");
                return;
            }

            if (hours < 0)
            {
                MessageBox.Show("Hours worked cannot be negative.");
                return;
            }

            if (dependents < 0)
            {
                MessageBox.Show("Dependents cannot be negative.");
                return;
            }

            if (dependents > 10)
            {
                MessageBox.Show("Dependents cannot exceed 10.");
                return;
            }

            // Calculations

            PayrollCalculator calc = new PayrollCalculator();

            double grossPay = calc.CalculateGrossPay(hours);

            double uif = calc.CalculateUIF(grossPay);

            double paye =
                calc.CalculatePAYE(grossPay, dependents);

            double membership =
                calc.CalculateMembership(grossPay);

            double totalDeductions =
                uif + paye + membership;

            double netPay =
                calc.CalculateNetPay(
                    grossPay,
                    uif,
                    paye,
                    membership);

            // Display Results

            textBox9.Text = "R " + grossPay.ToString("N2");
            textBox8.Text = "R " + paye.ToString("N2");
            textBox7.Text = "R " + uif.ToString("N2");
            textBox6.Text = "R " + membership.ToString("N2");
            textBox5.Text = "R " + totalDeductions.ToString("N2");
            textBox4.Text = "R " + netPay.ToString("N2");
        }





        private void button2_Click_1(object sender, EventArgs e)
        {
            textBox1.Clear();
            textBox2.Clear();
            textBox3.Clear();

            textBox4.Clear();
            textBox5.Clear();
            textBox6.Clear();
            textBox7.Clear();
            textBox8.Clear();
            textBox9.Clear();
        }

        private void button3_Click(object sender, EventArgs e)
        {
            Application.Exit();
        }
    }
}