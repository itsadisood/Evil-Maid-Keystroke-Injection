#include "stm32f0xx.h"
#include <stdint.h>

void init_usart5() {
    RCC->AHBENR |= RCC_AHBENR_GPIOCEN | RCC_AHBENR_GPIODEN;

    // PC12 → TX (AF2)
    GPIOC->MODER &= ~(3 << (12*2));
    GPIOC->MODER |=  (2 << (12*2));
    GPIOC->AFR[1] &= ~(0xF << (4*(12-8)));
    GPIOC->AFR[1] |=  (0x2 << (4*(12-8)));

    // PD2 → RX (AF2)
    GPIOD->MODER &= ~(3 << (2*2));
    GPIOD->MODER |=  (2 << (2*2));
    GPIOD->AFR[0] &= ~(0xF << (4*2));
    GPIOD->AFR[0] |=  (0x2 << (4*2));

    RCC->APB1ENR |= RCC_APB1ENR_USART5EN;

    USART5->CR1 &= ~USART_CR1_UE;
    USART5->CR1 &= ~USART_CR1_M;
    USART5->CR2 &= ~USART_CR2_STOP;
    USART5->CR1 &= ~USART_CR1_PCE;
    USART5->CR1 &= ~USART_CR1_OVER8;

    USART5->BRR = 48000000 / 115200;
    USART5->CR1 |= USART_CR1_TE | USART_CR1_RE | USART_CR1_UE;
}

void send_str(const char *s) {
    while (*s) {
        while (!(USART5->ISR & USART_ISR_TXE));
        USART5->TDR = *s++;
    }
}

void delay() {
    for(volatile int i = 0; i < 3000000; i++);
}

int main(void) {
    init_usart5();

    delay();

    send_str("WINR\n");
    delay();

    send_str("TYPE:cmd\n");
    delay();
    send_str("ENTER\n");
    delay();

    send_str("TYPE:echo Hello world from outside world > file.txt\n");
    delay();
    send_str("ENTER\n");
    delay();

    send_str("TYPE:code file.txt\n");
    delay();
    send_str("ENTER\n");

    while(1);
}
