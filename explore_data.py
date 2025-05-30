import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from load_data import load_ufc_data
import os

def analyze_fight_outcomes(df):
    """Analyze fight outcomes and generate visualizations."""
    # Create output directory for plots
    project_root = os.path.dirname(os.path.abspath(__file__))
    plots_dir = os.path.join(project_root, 'analysis_plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    # Fight outcomes distribution
    outcome_counts = df['status'].value_counts()
    plt.figure(figsize=(10, 6))
    outcome_counts.plot(kind='bar')
    plt.title('Distribution of Fight Outcomes')
    plt.xlabel('Outcome')
    plt.ylabel('Count')
    plt.savefig(os.path.join(plots_dir, 'fight_outcomes.png'))
    plt.close()
    
    print("\nFight Outcomes Distribution:")
    print(outcome_counts)
    print(f"\nWin Rate: {(outcome_counts['win'] / len(df) * 100):.1f}%")

def analyze_fighter_stats(df):
    """Analyze fighter statistics and generate visualizations."""
    plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analysis_plots')
    
    # Weight class distribution
    plt.figure(figsize=(12, 6))
    df['weight_class'].value_counts().plot(kind='bar')
    plt.title('Distribution of Weight Classes')
    plt.xlabel('Weight Class')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, 'weight_class_distribution.png'))
    plt.close()
    
    # Correlation between features
    numeric_cols = ['r_str', 'r_td', 'r_kd', 'r_career_fights', 
                   'r_career_wins', 'r_career_losses', 'r_career_win_rate']
    correlation = df[numeric_cols].corr()
    
    plt.figure(figsize=(12, 8))
    sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
    plt.title('Correlation between Fighter Features')
    plt.savefig(os.path.join(plots_dir, 'feature_correlation.png'))
    plt.close()
    
    print("\nFighter Statistics Summary:")
    print(df[numeric_cols].describe())

def analyze_winning_factors(df):
    """Analyze factors that contribute to winning."""
    plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analysis_plots')
    
    # Compare stats between winners and losers
    winner_stats = df[df['status'] == 'win']
    loser_stats = df[df['status'] == 'loss']
    
    # Strikes comparison
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=pd.DataFrame({
        'Winners': winner_stats['r_str'],
        'Losers': loser_stats['r_str']
    }))
    plt.title('Strikes: Winners vs Losers')
    plt.ylabel('Strikes Landed')
    plt.savefig(os.path.join(plots_dir, 'strikes_comparison.png'))
    plt.close()
    
    # Takedowns comparison
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=pd.DataFrame({
        'Winners': winner_stats['r_td'],
        'Losers': loser_stats['r_td']
    }))
    plt.title('Takedowns: Winners vs Losers')
    plt.ylabel('Takedowns Landed')
    plt.savefig(os.path.join(plots_dir, 'takedowns_comparison.png'))
    plt.close()
    
    # Knockdowns comparison
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=pd.DataFrame({
        'Winners': winner_stats['r_kd'],
        'Losers': loser_stats['r_kd']
    }))
    plt.title('Knockdowns: Winners vs Losers')
    plt.ylabel('Knockdowns')
    plt.savefig(os.path.join(plots_dir, 'knockdowns_comparison.png'))
    plt.close()
    
    print("\nWinning Factors Analysis:")
    print("\nAverage Strikes:")
    print(f"Winners: {winner_stats['r_str'].mean():.2f}")
    print(f"Losers: {loser_stats['r_str'].mean():.2f}")
    
    print("\nAverage Takedowns:")
    print(f"Winners: {winner_stats['r_td'].mean():.2f}")
    print(f"Losers: {loser_stats['r_td'].mean():.2f}")
    
    print("\nAverage Knockdowns:")
    print(f"Winners: {winner_stats['r_kd'].mean():.2f}")
    print(f"Losers: {loser_stats['r_kd'].mean():.2f}")

def main():
    # Load and process data
    df = load_ufc_data()
    
    # Perform analysis
    analyze_fight_outcomes(df)
    analyze_fighter_stats(df)
    analyze_winning_factors(df)
    
    print("\nAnalysis complete! Check the 'analysis_plots' directory for visualizations.")

if __name__ == "__main__":
    main()
